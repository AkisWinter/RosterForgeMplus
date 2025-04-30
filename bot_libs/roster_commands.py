### File: roster_commands.py

import discord
from discord import app_commands
from libs.utils import sanitize_charname, split_charname, build_char_id
from libs.sql_handler import Roster, RosterMember, CharacterProfile
from libs.character_service import fetch_character_info, persist_character

import json
with open("libs/realm_slug_map_eu.json", "r", encoding="utf-8") as f:
    REALM_SLUG_MAP = json.load(f)

def register_roster_commands(tree: discord.app_commands.CommandTree, db_handler, guild=None):
    
    @tree.command(name="roster_invites", description="List /inv lines for all members of a roster", guild=guild)
    @app_commands.describe(roster="Roster name")
    async def roster_invites(interaction: discord.Interaction, roster: str):
        session = db_handler.session
        r = session.query(Roster).filter_by(name=roster).first()
        if not r:
            await interaction.response.send_message(f"Roster '{roster}' not found.", ephemeral=True)
            return

        members = session.query(RosterMember).filter_by(roster_id=r.id).all()
        if not members:
            await interaction.response.send_message(f"Roster '{roster}' has no members.", ephemeral=True)
            return

        lines = [f"/inv {m.character_id}" for m in members]
        chunks, current = [], ""
        for line in lines:
            if len(current) + len(line) + 1 > 250:
                chunks.append(current.strip())
                current = ""
            current += line + "\n"
        if current:
            chunks.append(current.strip())

        output = "\n\n".join([f"```\n{block}\n```" for block in chunks])
        await interaction.response.send_message(output, ephemeral=True)

    @tree.command(name="create_roster", description="Create a new raid roster")
    @app_commands.describe(name="Roster name")
    async def create_roster(interaction: discord.Interaction, name: str):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You don't have permission to create a roster.", ephemeral=True)
            return

        session = db_handler.session
        exists = session.query(Roster).filter_by(name=name).first()
        if exists:
            await interaction.response.send_message(f"Roster '{name}' already exists.", ephemeral=True)
            return

        session.add(Roster(name=name, created_by=str(interaction.user.id)))
        session.commit()
        await interaction.response.send_message(f"✅ Roster '{name}' created.", ephemeral=True)

    @tree.command(name="delete_roster", description="Delete a raid roster")
    @app_commands.describe(name="Roster name")
    async def delete_roster(interaction: discord.Interaction, name: str):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You don't have permission to delete a roster.", ephemeral=True)
            return

        session = db_handler.session
        roster = session.query(Roster).filter_by(name=name).first()
        if not roster:
            await interaction.response.send_message(f"Roster '{name}' not found.", ephemeral=True)
            return

        session.query(RosterMember).filter_by(roster_id=roster.id).delete()
        session.delete(roster)
        session.commit()
        await interaction.response.send_message(f"✅ Roster '{name}' deleted.", ephemeral=True)

    @tree.command(name="list_rosters", description="List all raid rosters")
    async def list_rosters(interaction: discord.Interaction):
        session = db_handler.session
        rosters = session.query(Roster).all()
        if not rosters:
            await interaction.response.send_message("No rosters found.", ephemeral=True)
            return

        lines = [f"{r.name}" for r in rosters]
        await interaction.response.send_message("```\n" + "\n".join(lines) + "\n```", ephemeral=True)

    @tree.command(name="list_roster_members", description="List members in a raid roster with profile info")
    @app_commands.describe(name="Roster name")
    async def list_roster_members(interaction: discord.Interaction, name: str):
        session = db_handler.session
        roster = session.query(Roster).filter_by(name=name).first()
        if not roster:
            await interaction.response.send_message(f"Roster '{name}' not found.", ephemeral=True)
            return

        members = session.query(RosterMember).filter_by(roster_id=roster.id).all()
        if not members:
            await interaction.response.send_message(f"Roster '{name}' has no members.", ephemeral=True)
            return

        def resolve_raid_difficulty(ilvl):
            if ilvl is None:
                return "⚪----"
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
                return "⚪---"
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
        lines.append(" " * 73 + "|"+ " " * 11 + "Vault (🗝️ Raid / 🌀 M+)")
        lines.append(f"{'Name':<30} {'Role':<8} {'Class':<14} {'iLvl':<9} {'Score':<7} | {'Raid 1':<8}{'Raid 2':<8}{'Raid 3':<8} | {'M+ 1':<4} {' M+ 2':<4} {' M+ 3':<2}")
        lines.append("-" * 120)

        from libs.sql_handler import CharacterProfile

        for m in members:
            profile = session.query(CharacterProfile).filter_by(char_id=m.character_id).first()
            if profile:
                ilvl = f"{profile.equipped_item_level}/{profile.average_item_level}"
                raid1 = resolve_raid_difficulty(profile.raid_slot1_ilvl)
                raid2 = resolve_raid_difficulty(profile.raid_slot2_ilvl)
                raid3 = resolve_raid_difficulty(profile.raid_slot3_ilvl)
                v1 = color_mplus(profile.vault_slot1_ilvl)
                v2 = color_mplus(profile.vault_slot2_ilvl)
                v3 = color_mplus(profile.vault_slot3_ilvl)

                line = f"{profile.char_id:<30} {m.role:<8} {profile.class_name:<14} {ilvl:<9} {profile.mythic_plus_score:<7} | {raid1:<6} {raid2:<6} {raid3:<6} | {v1:<4} {v2:<4} {v3:<2}"
            else:
                line = f"{m.character_id:<30} {'?':<8} {'?':<14} {'?':<9} {'?':<7} | {'?':<6} {'?':<6} {'?':<6} | {'?':<4} {'?':<4} {'?':<2}"

            lines.append(line)

        lines.append("\nLegend:")
        lines.append("🔶 Mythic / 662+ | 🟣 Heroic / 649+ | 🔵 Normal / 636+ | 🟢 LFR / 623+")
        output = "```text\n" + "\n".join(lines) + "\n```"
        # Nachricht splitten, wenn zu lang
        MAX_LENGTH = 1800  # Sicherheitsreserve für Markdown/Codeblocks
        blocks = []
        buffer = ""
        
        for line in lines:
            if len(buffer) + len(line) + 1 > MAX_LENGTH:
                blocks.append("```text\n" + buffer + "\n```")
                buffer = ""
            buffer += line + "\n"
        
        if buffer:
            blocks.append("```text\n" + buffer + "\n```")
        
        # Erste Nachricht als Antwort, Rest als Followups
        await interaction.response.send_message(blocks[0], ephemeral=True)
        for block in blocks[1:]:
            await interaction.followup.send(block, ephemeral=True)
    
    @tree.command(name="add_to_roster", description="Add a character to a roster (includes profile fetch)", guild=guild)
    @app_commands.describe(
        roster="Roster name",
        char="Character name with realm (e.g. Akisfury-Blackrock)",
        role="Character role in raid"
    )
    @app_commands.choices(role=[
        app_commands.Choice(name="Tank", value="Tank"),
        app_commands.Choice(name="Healer", value="Healer"),
        app_commands.Choice(name="DPS", value="DPS"),
    ])
    async def add_to_roster(interaction: discord.Interaction, roster: str, char: str, role: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)
        session = db_handler.session
        user_id = str(interaction.user.id)

        r = session.query(Roster).filter_by(name=roster).first()
        if not r:
            await interaction.followup.send(f"❌ Roster '{roster}' not found.", ephemeral=True)
            return

        char = sanitize_charname(char)
        name_realm = split_charname(char)
        if not name_realm:
            await interaction.followup.send("❌ Invalid format. Use Name-Realm.", ephemeral=True)
            return

        name, realm = name_realm
        realm_slug = REALM_SLUG_MAP.get(realm)
        if not realm_slug:
            await interaction.followup.send(f"❌ Unknown realm '{realm}'.", ephemeral=True)
            return

        try:
            info = fetch_character_info(realm_slug.lower(), name.lower())
            char_id = build_char_id(info['name'], info['realm'])
            info['char_id'] = char_id

            vault = info.pop('vault_rewards', [{}]*3)
            for i, v in enumerate(vault, start=1):
                info[f'vault_slot{i}_key'] = v.get('key_level')
                info[f'vault_slot{i}_ilvl'] = v.get('item_level')

            raid = info.pop('raid_rewards', [{}]*3)
            for i, rwd in enumerate(raid, start=1):
                info[f'raid_slot{i}_ilvl'] = rwd.get('item_level')

            persist_character(session, user_id, char_id, info)

            exists = session.query(RosterMember).filter_by(roster_id=r.id, character_id=char_id).first()
            if exists:
                await interaction.followup.send(f"⚠️ {char_id} is already in '{roster}'.", ephemeral=True)
                return

            session.add(RosterMember(roster_id=r.id, character_id=char_id, role=role.value))
            session.commit()
            await interaction.followup.send(f"✅ {char_id} added to roster '{roster}' as {role.value}.", ephemeral=True)

        except Exception as e:
            session.rollback()
            await interaction.followup.send(f"❌ Error while adding to roster: {e}", ephemeral=True)