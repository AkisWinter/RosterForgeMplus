import os
import json
import discord
from discord.ext import commands
from discord import app_commands
from libs.sql_handler import SQLHandler, TrackedGuild, UserCharacter, Rooster, RoosterMember, CharacterProfile
from libs.blizzard_api_handler import BlizzardAPIClient
from libs.raiderio_api_handler import RaiderIOAPIClient
from libs.character_profile_parser import CharacterProfileParser
from config import (
    DISCORD_TOKEN, DATABASE_URL,
    CLIENT_ID, CLIENT_SECRET, REGION, LOCALE,
    USE_RAIDERIO_FOR_MPLUS, RAIDERIO_ACCESS_KEY,
    MYTHIC_PLUS_MAPPING, RAID_MAPPING, ACTIVE_RAID_NAME
)

with open("libs/realm_slug_map_eu.json", "r", encoding="utf-8") as f:
    REALM_SLUG_MAP = json.load(f)
    
# Initialize database handler
db_handler = SQLHandler(DATABASE_URL)

# Discord Bot Setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot ready as {bot.user}")

# Slash Command: /add_guild
@tree.command(name="add_guild", description="Track a new guild")
@app_commands.describe(guildname="Guild name", guildrealm="Guild realm")
async def add_guild(interaction: discord.Interaction, guildname: str, guildrealm: str):
    if db_handler.add_tracked_guild(guildname, guildrealm):
        await interaction.response.send_message(f"Guild '{guildname}-{guildrealm}' added for tracking.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Guild '{guildname}-{guildrealm}' is already tracked.", ephemeral=True)

# Slash Command: /remove_guild
@tree.command(name="remove_guild", description="Stop tracking a guild")
@app_commands.describe(guildname="Guild name", guildrealm="Guild realm")
async def remove_guild(interaction: discord.Interaction, guildname: str, guildrealm: str):
    if db_handler.remove_tracked_guild(guildname, guildrealm):
        await interaction.response.send_message(f"Guild '{guildname}-{guildrealm}' removed from tracking.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Guild '{guildname}-{guildrealm}' was not tracked.", ephemeral=True)

# Slash Command: /list_guilds
@tree.command(name="list_guilds", description="List all tracked guilds")
async def list_guilds(interaction: discord.Interaction):
    session = db_handler.session
    guilds = session.query(TrackedGuild).all()
    if not guilds:
        await interaction.response.send_message("No guilds are currently tracked.", ephemeral=True)
    else:
        guild_list = "\n".join([f"- {g.name} ({g.realm})" for g in guilds])
        await interaction.response.send_message(f"**Tracked Guilds:**\n{guild_list}", ephemeral=True)

# Slash Command: /add_char
@tree.command(name="add_char", description="Link your WoW character and fetch profile")
@app_commands.describe(char="Character name with realm (e.g. Akisfury-Blackrock)")
async def add_char(interaction: discord.Interaction, char: str):
    await interaction.response.defer(ephemeral=True)  # Typisches Discord-Delay-Handling

    session = db_handler.session
    user_id = str(interaction.user.id)
    char = char.replace(" ", "").replace("'", "")

    if "-" not in char:
        await interaction.followup.send("❌ Invalid character format. Use Name-Realm, e.g. Akisfury-Blackrock.", ephemeral=True)
        return

    name, compact_realm = char.split("-", 1)
    realm_slug = REALM_SLUG_MAP.get(compact_realm)

    if not realm_slug:
        await interaction.followup.send(f"❌ Realm '{compact_realm}' is not recognized.", ephemeral=True)
        return

    safe_name = name.lower()
    safe_realm = realm_slug.lower()

    try:
        blizzard = BlizzardAPIClient(CLIENT_ID, CLIENT_SECRET, REGION, LOCALE)

        # Blizzard Profile
        profile_data = blizzard.get_character_profile(safe_realm, safe_name)

        # M+ Data
        if USE_RAIDERIO_FOR_MPLUS:
            raider = RaiderIOAPIClient(REGION, RAIDERIO_ACCESS_KEY)
            keystone_data = raider.get_mythic_plus_profile(profile_data['realm']['name'], profile_data['name'])
        else:
            keystone_data = blizzard.get_mythic_keystone_profile(safe_realm, safe_name)

        raid_data = blizzard.get_character_raid_profile(safe_realm, safe_name)

        parser = CharacterProfileParser(
            profile_data, keystone_data, raid_data,
            debug=False,
            keystone_reward_mapping=MYTHIC_PLUS_MAPPING,
            raid_reward_mapping=RAID_MAPPING,
            active_raid_name=ACTIVE_RAID_NAME
        )
        character_info = parser.extract_character_info()
        char_id = character_info['name'] + "-" + character_info['realm']
        char_id = char_id.replace(" ", "").replace("'", "")
        character_info["char_id"] = char_id

        # Vault + Raid Mapping
        vault = character_info.pop('vault_rewards', [{}] * 3)
        character_info.update({
            'vault_slot1_key': vault[0].get('key_level'),
            'vault_slot1_ilvl': vault[0].get('item_level'),
            'vault_slot2_key': vault[1].get('key_level'),
            'vault_slot2_ilvl': vault[1].get('item_level'),
            'vault_slot3_key': vault[2].get('key_level'),
            'vault_slot3_ilvl': vault[2].get('item_level'),
        })

        raid = character_info.pop('raid_rewards', [{}] * 3)
        character_info.update({
            'raid_slot1_ilvl': raid[0].get('item_level'),
            'raid_slot2_ilvl': raid[1].get('item_level'),
            'raid_slot3_ilvl': raid[2].get('item_level'),
        })

        # Add or update in DB
        existing = session.query(UserCharacter).filter_by(discord_id=user_id, character_id=char_id).first()
        if not existing:
            session.add(UserCharacter(discord_id=user_id, character_id=char_id))

        from libs.sql_handler import CharacterProfile, CharacterSnapshot
        existing_profile = session.query(CharacterProfile).filter_by(char_id=char_id).first()
        if existing_profile:
            for key, value in character_info.items():
                if hasattr(existing_profile, key):
                    setattr(existing_profile, key, value)
        else:
            session.add(CharacterProfile(**character_info))

        session.add(CharacterSnapshot(**character_info))
        session.commit()

        await interaction.followup.send(f"✅ Character {char_id} has been linked and profile data stored.", ephemeral=True)

    except Exception as e:
        session.rollback()
        await interaction.followup.send(f"❌ Failed to fetch character data: {e}", ephemeral=True)

# Slash Command: /list_chars
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


def get_raid_difficulty(ilvl):
    # Map your RAID_MAPPING from config.py
    from config import RAID_MAPPING
    for difficulty, val in RAID_MAPPING.items():
        if val == ilvl:
            return difficulty
    return "?"


# Slash Command: /create_rooster
@tree.command(name="create_rooster", description="Create a raid rooster")
@app_commands.describe(name="Name of the rooster")
async def create_rooster(interaction: discord.Interaction, name: str):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("You don't have permission to create a rooster.", ephemeral=True)
        return
    session = db_handler.session
    exists = session.query(Rooster).filter_by(name=name).first()
    if exists:
        await interaction.response.send_message(f"Rooster '{name}' already exists.", ephemeral=True)
    else:
        rooster = Rooster(name=name, created_by=str(interaction.user.id))
        session.add(rooster)
        session.commit()
        await interaction.response.send_message(f"Rooster '{name}' created.", ephemeral=True)

# Slash Command: /add_to_rooster
@tree.command(name="add_to_rooster", description="Add character to a rooster and fetch profile")
@app_commands.describe(roostername="Rooster name", charname="Character name with realm")
async def add_to_rooster(interaction: discord.Interaction, roostername: str, charname: str):
    await interaction.response.defer(ephemeral=True)

    session = db_handler.session
    rooster = session.query(Rooster).filter_by(name=roostername).first()
    charname = charname.replace(" ", "").replace("'", "")

    if not rooster:
        await interaction.followup.send(f"❌ Rooster '{roostername}' not found.", ephemeral=True)
        return

    if "-" not in charname:
        await interaction.followup.send("❌ Invalid format. Use Name-Realm (e.g. Akisfury-Blackrock).", ephemeral=True)
        return

    name, compact_realm = charname.split("-", 1)
    realm_slug = REALM_SLUG_MAP.get(compact_realm)
    if not realm_slug:
        await interaction.followup.send(f"❌ Realm '{compact_realm}' is not recognized.", ephemeral=True)
        return

    safe_name = name.lower()
    safe_realm = realm_slug.lower()

    try:
        blizzard = BlizzardAPIClient(CLIENT_ID, CLIENT_SECRET, REGION, LOCALE)

        profile_data = blizzard.get_character_profile(safe_realm, safe_name)

        if USE_RAIDERIO_FOR_MPLUS:
            raider = RaiderIOAPIClient(REGION, RAIDERIO_ACCESS_KEY)
            keystone_data = raider.get_mythic_plus_profile(profile_data['realm']['name'], profile_data['name'])
        else:
            keystone_data = blizzard.get_mythic_keystone_profile(safe_realm, safe_name)

        raid_data = blizzard.get_character_raid_profile(safe_realm, safe_name)

        parser = CharacterProfileParser(
            profile_data, keystone_data, raid_data,
            debug=False,
            keystone_reward_mapping=MYTHIC_PLUS_MAPPING,
            raid_reward_mapping=RAID_MAPPING,
            active_raid_name=ACTIVE_RAID_NAME
        )
        character_info = parser.extract_character_info()
        char_id = character_info['name'] + "-" + character_info['realm']
        char_id = char_id.replace(" ", "").replace("'", "")
        character_info["char_id"] = char_id

        # Vault + Raid Mapping
        vault = character_info.pop('vault_rewards', [{}] * 3)
        character_info.update({
            'vault_slot1_key': vault[0].get('key_level'),
            'vault_slot1_ilvl': vault[0].get('item_level'),
            'vault_slot2_key': vault[1].get('key_level'),
            'vault_slot2_ilvl': vault[1].get('item_level'),
            'vault_slot3_key': vault[2].get('key_level'),
            'vault_slot3_ilvl': vault[2].get('item_level'),
        })

        raid = character_info.pop('raid_rewards', [{}] * 3)
        character_info.update({
            'raid_slot1_ilvl': raid[0].get('item_level'),
            'raid_slot2_ilvl': raid[1].get('item_level'),
            'raid_slot3_ilvl': raid[2].get('item_level'),
        })

        from libs.sql_handler import CharacterProfile, CharacterSnapshot
        existing_profile = session.query(CharacterProfile).filter_by(char_id=char_id).first()
        if existing_profile:
            for key, value in character_info.items():
                if hasattr(existing_profile, key):
                    setattr(existing_profile, key, value)
        else:
            session.add(CharacterProfile(**character_info))

        session.add(CharacterSnapshot(**character_info))
        session.commit()

        # Rooster-Eintrag prüfen
        exists = session.query(RoosterMember).filter_by(rooster_id=rooster.id, character_id=char_id).first()
        if exists:
            await interaction.followup.send(f"Character {char_id} is already in rooster '{roostername}'.", ephemeral=True)
            return

        session.add(RoosterMember(rooster_id=rooster.id, character_id=char_id))
        session.commit()

        await interaction.followup.send(f"✅ Added {char_id} to rooster '{roostername}' and profile updated.", ephemeral=True)

    except Exception as e:
        session.rollback()
        await interaction.followup.send(f"❌ Failed to process character: {e}", ephemeral=True)


# Slash Command: /remove_from_rooster
@tree.command(name="remove_from_rooster", description="Remove character from a rooster")
@app_commands.describe(roostername="Rooster name", charname="Character name with realm")
async def remove_from_rooster(interaction: discord.Interaction, roostername: str, charname: str):
    session = db_handler.session
    rooster = session.query(Rooster).filter_by(name=roostername).first()
    charname = charname.replace(" ", "").replace("'", "")
    if not rooster:
        await interaction.response.send_message(f"Rooster '{roostername}' not found.", ephemeral=True)
        return
    deleted = session.query(RoosterMember).filter_by(rooster_id=rooster.id, character_id=charname).delete()
    session.commit()
    if deleted:
        await interaction.response.send_message(f"Removed {charname} from rooster '{roostername}'.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Character not found in rooster.", ephemeral=True)

# Slash Command: /delete_rooster
@tree.command(name="delete_rooster", description="Delete a raid rooster")
@app_commands.describe(name="Name of the rooster")
async def delete_rooster(interaction: discord.Interaction, name: str):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("You don't have permission to delete a rooster.", ephemeral=True)
        return
    session = db_handler.session
    rooster = session.query(Rooster).filter_by(name=name).first()
    if not rooster:
        await interaction.response.send_message(f"Rooster '{name}' does not exist.", ephemeral=True)
        return
    session.query(RoosterMember).filter_by(rooster_id=rooster.id).delete()
    session.delete(rooster)
    session.commit()
    await interaction.response.send_message(f"Rooster '{name}' deleted.", ephemeral=True)

# Slash Command: /list_roosters
@tree.command(name="list_roosters", description="List all raid roosters")
async def list_roosters(interaction: discord.Interaction):
    session = db_handler.session
    roosters = session.query(Rooster).all()
    if not roosters:
        await interaction.response.send_message("No roosters found.", ephemeral=True)
    else:
        rooster_list = "\n".join([f"- {r.name}" for r in roosters])
        await interaction.response.send_message(f"**Raid Roosters:**\n{rooster_list}", ephemeral=True)

# Slash Command: /list_rooster_members
@tree.command(name="list_rooster_members", description="List members of a raid rooster with full profile info")
@app_commands.describe(roostername="Rooster name")
async def list_rooster_members(interaction: discord.Interaction, roostername: str):
    session = db_handler.session
    rooster = session.query(Rooster).filter_by(name=roostername).first()

    if not rooster:
        await interaction.response.send_message(f"Rooster '{roostername}' not found.", ephemeral=True)
        return

    members = session.query(RoosterMember).filter_by(rooster_id=rooster.id).all()

    if not members:
        await interaction.response.send_message(f"No members found for rooster '{roostername}'.", ephemeral=True)
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
    lines.append(" " * 64 + "|" + " " * 11 + "Vault (🗝️ Raid / 🌀 M+)")
    lines.append(f"{'Name':<30} {'Class':<14} {'iLvl':<9} {'Score':<7} | {'Raid 1':<7} {'Raid 2':<7}  {'Raid 3':<2} | {'M+ 1':<4} {' M+ 2':<4} {' M+ 3':<2}")
    lines.append("-" * 110)

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

            line = f"{profile.char_id:<30} {profile.class_name:<14} {ilvl:<9} {profile.mythic_plus_score:<7} | {raid1:<6} {raid2:<6} {raid3:<2} | {v1:<4} {v2:<4} {v3:<2}"
        else:
            line = f"{m.character_id:<30} {'?':<14} {'?':<9} {'?':<7} | {'?':<6} {'?':<6} {'?':<2} | {'?':<4} {'?':<4} {'?':<2}"

        lines.append(line)

    lines.append("\nLegend:")
    lines.append("🔶 Mythic / 662+ | 🟣 Heroic / 649+ | 🔵 Normal / 636+ | 🟢 LFR / 623+")

    output = "```text\n" + "\n".join(lines) + "\n```"
    await interaction.response.send_message(output, ephemeral=True)


if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
