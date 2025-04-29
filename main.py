from libs.blizzard_api_handler import BlizzardAPIClient
from libs.character_profile_parser import CharacterProfileParser
from libs.sql_handler import SQLHandler
from config import DATABASE_URL, CLIENT_ID, CLIENT_SECRET, REGION, REALM_SLUG, LOCALE, MYTHIC_PLUS_MAPPING, RAID_MAPPING, ACTIVE_RAID_NAME, GUILD_NAME
from urllib.parse import quote
import json
import os

def save_json(data, filename):
    SAVE_FOLDER = "saved_profiles"
    os.makedirs(SAVE_FOLDER, exist_ok=True)
    with open(os.path.join(SAVE_FOLDER, filename), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def main():
    # Step 1: Connect to Blizzard API
    api_client = BlizzardAPIClient(CLIENT_ID, CLIENT_SECRET, REGION, LOCALE)

    # Step 2: Connect to Database
    db_handler = SQLHandler(DATABASE_URL)
    db_handler.create_tables()

    # Step 3: Fetch Guild Roster
    roster = api_client.get_guild_roster(REALM_SLUG, GUILD_NAME)

    # Step 4: Process each character
    for member in roster:
        character = member.get('character', {})
        character_name = character.get('name')
        character_realm = character.get('realm', {}).get('slug', REALM_SLUG)

        try:
            safe_name = quote(character_name.lower())
            safe_realm = quote(character_realm.lower())

            profile_data = api_client.get_character_profile(safe_realm, safe_name)
            keystone_data = api_client.get_mythic_keystone_profile(safe_realm, safe_name)
            raid_data = api_client.get_character_raid_profile(safe_realm, safe_name)

            # Save raw JSONs for debug / archive
            # save_json(profile_data, f"{character_name}_profile.json")
            # save_json(keystone_data, f"{character_name}_keystone.json")
            # save_json(raid_data, f"{character_name}_raids.json")

            parser = CharacterProfileParser(
                profile_data,
                keystone_data,
                raid_data,
                debug=True,
                keystone_reward_mapping=MYTHIC_PLUS_MAPPING,
                raid_reward_mapping=RAID_MAPPING,
                active_raid_name=ACTIVE_RAID_NAME
            )

            character_info = parser.extract_character_info()

            db_handler.insert_character_info(character_info)
            db_handler.record_character_snapshot(character_info)

        except Exception as e:
            print(f"Failed to process {character_name}: {e}")

    # Optional: Fetch and display all characters
    all_characters = db_handler.fetch_all_characters()
    for char in all_characters:
        print(char)

if __name__ == "__main__":
    main()
