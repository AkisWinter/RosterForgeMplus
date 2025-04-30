import discord
from discord import app_commands
from libs.utils import sanitize_charname, split_charname, build_char_id
from libs.character_service import fetch_character_info, persist_character
from libs.sql_handler import CharacterProfile, UserCharacter

import json
with open("libs/realm_slug_map_eu.json", "r", encoding="utf-8") as f:
    REALM_SLUG_MAP = json.load(f)

def register_char_commands(tree: discord.app_commands.CommandTree, db_handler, guild=None):

    async def handle_character_link(interaction, session, user_id, name, realm):
        realm_slug = REALM_SLUG_MAP.get(realm)
        if not realm_slug:
            await interaction.followup.send(f"❌ Unknown realm '{realm}'.", ephemeral=True)
            return None

        try:
            info = fetch_character_info(realm_slug.lower(), name.lower())
            char_id = build_char_id(info['name'], info['realm'])
            info['char_id'] = char_id

            vault = info.pop('vault_rewards', [{}]*3)
            for i, v in enumerate(vault, start=1):
                info[f'vault_slot{i}_key'] = v.get('key_level')
                info[f'vault_slot{i}_ilvl'] = v.get('item_level')

            raid = info.pop('raid_rewards', [{}]*3)
            for i, r in enumerate(raid, start=1):
                info[f'raid_slot{i}_ilvl'] = r.get('item_level')

            persist_character(session, user_id, char_id, info)
            return char_id

        except Exception as e:
            session.rollback()
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
            return None

    @tree.command(name="add_char", description="Link your WoW character and fetch profile")
    @app_commands.describe(char="Character name with realm (e.g. Akisfury-Blackrock)")
    async def add_char(interaction: discord.Interaction, char: str):
        await interaction.response.defer(ephemeral=True)
        session = db_handler.session
        user_id = str(interaction.user.id)

        char = sanitize_charname(char)
        name_realm = split_charname(char)
        if not name_realm:
            await interaction.followup.send("❌ Invalid format. Use Name-Realm.", ephemeral=True)
            return

        name, realm = name_realm
        char_id = await handle_character_link(interaction, session, user_id, name, realm)
        if char_id:
            await interaction.followup.send(f"✅ Character {char_id} linked and data stored.", ephemeral=True)

    @tree.command(name="remove_char", description="Unlink a WoW character")
    @app_commands.describe(char="Character name with realm (e.g. Akisfury-Blackrock)")
    async def remove_char(interaction: discord.Interaction, char: str):
        session = db_handler.session
        user_id = str(interaction.user.id)
        char = sanitize_charname(char)
        deleted = session.query(UserCharacter).filter_by(discord_id=user_id, character_id=char).delete()
        session.commit()
        if deleted:
            await interaction.response.send_message(f"Character {char} has been removed from your account.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Character {char} was not linked to your account.", ephemeral=True)

    @tree.command(name="list_chars", description="List your linked WoW characters with profile info")
    async def list_chars(interaction: discord.Interaction):
        session = db_handler.session
        user_id = str(interaction.user.id)
        chars = session.query(UserCharacter).filter_by(discord_id=user_id).all()

        if not chars:
            await interaction.response.send_message("You have no linked characters.", ephemeral=True)
            return

        def resolve_raid_difficulty(ilvl):
            if ilvl is None:
                return "–"
            elif ilvl >= 662:
                return "🔶Myth"
            elif ilvl >= 649:
                return "🟣Hero"
            elif ilvl >= 636:
                return "🔵Norm"
            elif ilvl >= 623:
                return "🟢LFR"
            return "–"

        def color_mplus(ilvl):
            if ilvl is None:
                return "–     "
            if ilvl >= 662:
                return f"🔶{ilvl}"
            elif ilvl >= 649:
                return f"🟣{ilvl}"
            elif ilvl >= 636:
                return f"🔵{ilvl}"
            elif ilvl >= 623:
                return f"🟢{ilvl}"
            return f"{ilvl}"

        lines = []
        lines.append(" " * 64 + "|"+ " " * 11 + "Vault (🗝️ Raid / 🌀 M+)")
        lines.append(f"{'Name':<30} {'Class':<14} {'iLvl':<9} {'Score':<7} | {'Raid 1':<7} {'Raid 2':<7}  {'Raid 3':<2} | {'M+ 1':<4} {' M+ 2':<4} {' M+ 3':<2}")
        lines.append("-" * 110)

        for c in chars:
            profile = session.query(CharacterProfile).filter_by(char_id=c.character_id).first()

            if profile:
                ilvl = f"{profile.equipped_item_level}/{profile.average_item_level}"
                raid1 = resolve_raid_difficulty(profile.raid_slot1_ilvl)
                raid2 = resolve_raid_difficulty(profile.raid_slot2_ilvl)
                raid3 = resolve_raid_difficulty(profile.raid_slot3_ilvl)
                v1 = color_mplus(profile.vault_slot1_ilvl)
                v2 = color_mplus(profile.vault_slot2_ilvl)
                v3 = color_mplus(profile.vault_slot3_ilvl)

                line = f"{profile.char_id:<30} {profile.class_name:<14} {ilvl:<9} {profile.mythic_plus_score:<7} | {raid1:<6} {raid2:<6} {raid3:<2} | {v1:<4} {v2:<4} {v3:<2}"
            else:
                line = f"{c.character_id:<30} {'?':<14} {'?':<9} {'?':<7} | {'?':<6} {'?':<6} {'?':<2} | {'?':<4} {'?':<4} {'?':<2}"

            lines.append(line)

        lines.append("\nLegend:")
        lines.append("🔶 Mythic / 662+ | 🟣 Heroic / 649+ | 🔵 Normal / 636+ | 🟢 LFR / 623+")
        output = "```text\n" + "\n".join(lines) + "\n```"
        await interaction.response.send_message(output, ephemeral=True)
