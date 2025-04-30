from libs.blizzard_api_handler import BlizzardAPIClient
from libs.raiderio_api_handler import RaiderIOAPIClient
from libs.character_profile_parser import CharacterProfileParser
from libs.sql_handler import CharacterProfile, CharacterSnapshot, UserCharacter
from config import (
    CLIENT_ID, CLIENT_SECRET, REGION, LOCALE,
    USE_RAIDERIO_FOR_MPLUS, RAIDERIO_ACCESS_KEY,
    MYTHIC_PLUS_MAPPING, RAID_MAPPING, ACTIVE_RAID_NAME
)

def fetch_character_info(realm_slug: str, char_name: str) -> dict:
    blizzard = BlizzardAPIClient(CLIENT_ID, CLIENT_SECRET, REGION, LOCALE)
    profile_data = blizzard.get_character_profile(realm_slug, char_name)

    if USE_RAIDERIO_FOR_MPLUS:
        raider = RaiderIOAPIClient(REGION, RAIDERIO_ACCESS_KEY)
        keystone_data = raider.get_mythic_plus_profile(profile_data['realm']['name'], profile_data['name'])
    else:
        keystone_data = blizzard.get_mythic_keystone_profile(realm_slug, char_name)

    raid_data = blizzard.get_character_raid_profile(realm_slug, char_name)

    parser = CharacterProfileParser(
        profile_data, keystone_data, raid_data,
        debug=False,
        keystone_reward_mapping=MYTHIC_PLUS_MAPPING,
        raid_reward_mapping=RAID_MAPPING,
        active_raid_name=ACTIVE_RAID_NAME
    )

    return parser.extract_character_info()

def persist_character(session, user_id: str, char_id: str, character_info: dict):
    existing = session.query(UserCharacter).filter_by(discord_id=user_id, character_id=char_id).first()
    if not existing:
        session.add(UserCharacter(discord_id=user_id, character_id=char_id))

    existing_profile = session.query(CharacterProfile).filter_by(char_id=char_id).first()
    if existing_profile:
        for k, v in character_info.items():
            if hasattr(existing_profile, k):
                setattr(existing_profile, k, v)
    else:
        session.add(CharacterProfile(**character_info))

    session.add(CharacterSnapshot(**character_info))
    session.commit()
