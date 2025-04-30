
import os
import json
import time
from urllib.parse import quote
from config import DATABASE_URL, CLIENT_ID, CLIENT_SECRET, REGION, LOCALE, MYTHIC_PLUS_MAPPING, RAID_MAPPING, ACTIVE_RAID_NAME, USE_RAIDERIO_FOR_MPLUS, RAIDERIO_ACCESS_KEY
from libs.sql_handler import SQLHandler, TrackedGuild, UserCharacter, RoosterMember, CharacterProfile, CharacterSnapshot
from libs.blizzard_api_handler import BlizzardAPIClient
from libs.character_profile_parser import CharacterProfileParser
from libs.raiderio_api_handler import RaiderIOAPIClient
from sqlalchemy import exists

with open("libs/realm_slug_map_eu.json", "r", encoding="utf-8") as f:
    REALM_SLUG_MAP = json.load(f)

def collect_unique_characters(db_handler):
    session = db_handler.session
    characters = set()

    guilds = session.query(TrackedGuild).all()
    api_client = BlizzardAPIClient(CLIENT_ID, CLIENT_SECRET, REGION, LOCALE)
    for guild in guilds:
        try:
            roster = api_client.get_guild_roster(guild.realm.lower().replace(" ", "-"), guild.name.lower().replace(" ", "-"))
            for member in roster:
                char = member.get('character', {})
                name = char.get('name')
                realm_slug = char.get('realm', {}).get('slug')
                if name and realm_slug:
                    compact_realm = realm_slug.replace("-", "").title()
                    characters.add(f"{name}-{compact_realm}")
        except Exception as e:
            print(f"❌ Failed to fetch roster for guild {guild.name} ({guild.realm}): {e}")

    users = session.query(UserCharacter).all()
    for user_char in users:
        characters.add(user_char.character_id)

    rooster_members = session.query(RoosterMember).all()
    for member in rooster_members:
        characters.add(member.character_id)

    return characters

def process_characters(db_handler, characters):
    api_client = BlizzardAPIClient(CLIENT_ID, CLIENT_SECRET, REGION, LOCALE)

    if USE_RAIDERIO_FOR_MPLUS:
        raider_client = RaiderIOAPIClient(region=REGION, access_key=RAIDERIO_ACCESS_KEY)

    for char_id in characters:
        try:
            if "-" not in char_id:
                print(f"⚠️ Invalid char_id format: {char_id}. Skipping.")
                continue

            name, compact_realm = char_id.split("-", 1)
            realm_slug = REALM_SLUG_MAP.get(compact_realm)

            if not realm_slug:
                print(f"❌ Realm '{compact_realm}' not found in slug map! Please add it.")
                continue

            safe_name = quote(name.lower())
            safe_realm = quote(realm_slug.lower())

            print(f"🔍 Fetching profile for: name='{name}', realm_slug='{realm_slug}'")

            try:
                profile_data = api_client.get_character_profile(safe_realm, safe_name)
            except Exception as e:
                print(f"⚠️ Character {char_id} not found on Blizzard API. Skipping. ({e})")
                continue

            keystone_data = {}
            if USE_RAIDERIO_FOR_MPLUS:
                try:
                    keystone_data = raider_client.get_mythic_plus_profile(profile_data['realm']['name'], profile_data['name'])
                except Exception as e:
                    print(f"⚠️ Failed to fetch M+ profile for {char_id}: {e}")
            else:
                keystone_data = api_client.get_mythic_keystone_profile(safe_realm, safe_name)

            raid_data = api_client.get_character_raid_profile(safe_realm, safe_name)

            parser = CharacterProfileParser(
                profile_data,
                keystone_data,
                raid_data,
                debug=False,
                keystone_reward_mapping=MYTHIC_PLUS_MAPPING,
                raid_reward_mapping=RAID_MAPPING,
                active_raid_name=ACTIVE_RAID_NAME
            )

            character_info = parser.extract_character_info()
            char_id_clean = f"{character_info['name']}-{character_info['realm']}".replace(" ", "").replace("'", "")
            character_info["char_id"] = char_id_clean

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

            session = db_handler.session
            existing = session.query(CharacterProfile).filter_by(char_id=char_id_clean).first()
            if existing:
                for key, value in character_info.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                session.add(CharacterProfile(**character_info))

            session.add(CharacterSnapshot(**character_info))
            session.commit()

            print(f"✅ Processed {char_id_clean}")

        except Exception as e:
            print(f"❌ Failed to process {char_id}: {e}")

def main():
    db_handler = SQLHandler(DATABASE_URL)
    db_handler.create_tables()

    print("🔍 Collecting unique characters...")
    characters = collect_unique_characters(db_handler)
    print(f"➡️ {len(characters)} unique characters found.")

    print("🚀 Processing characters...")
    process_characters(db_handler, characters)

if __name__ == "__main__":
    main()
