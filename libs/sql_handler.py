from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class CharacterProfile(Base):
    __tablename__ = 'character_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    char_id = Column(String(250), nullable=False)
    name = Column(String(100))
    realm = Column(String(100))
    guild = Column(String(100))
    level = Column(Integer)
    equipped_item_level = Column(Integer)
    average_item_level = Column(Integer)
    mythic_plus_score = Column(Float)
    achievement_points = Column(Integer)
    vault_slot1_key = Column(Integer)
    vault_slot1_ilvl = Column(Integer)
    vault_slot2_key = Column(Integer)
    vault_slot2_ilvl = Column(Integer)
    vault_slot3_key = Column(Integer)
    vault_slot3_ilvl = Column(Integer)
    raid_slot1_ilvl = Column(Integer)
    raid_slot2_ilvl = Column(Integer)
    raid_slot3_ilvl = Column(Integer)

class CharacterSnapshot(Base):
    __tablename__ = 'character_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    char_id = Column(String(250), nullable=False)
    name = Column(String(100))
    realm = Column(String(100))
    guild = Column(String(100))
    level = Column(Integer)
    equipped_item_level = Column(Integer)
    average_item_level = Column(Integer)
    mythic_plus_score = Column(Float)
    achievement_points = Column(Integer)
    vault_slot1_key = Column(Integer)
    vault_slot1_ilvl = Column(Integer)
    vault_slot2_key = Column(Integer)
    vault_slot2_ilvl = Column(Integer)
    vault_slot3_key = Column(Integer)
    vault_slot3_ilvl = Column(Integer)
    raid_slot1_ilvl = Column(Integer)
    raid_slot2_ilvl = Column(Integer)
    raid_slot3_ilvl = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

class SQLHandler:
    def __init__(self, database_url):
        self.database_url = database_url
        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def create_tables(self):
        Base.metadata.create_all(self.engine)
        print("Tables created successfully.")

    def insert_character_info(self, character_info):
        try:
            char_id = character_info['name'] + "-" + character_info['realm']
            character = CharacterProfile(
                char_id=char_id,
                name=character_info['name'],
                realm=character_info['realm'],
                guild=character_info.get('guild'),
                level=character_info['level'],
                equipped_item_level=character_info['equipped_item_level'],
                average_item_level=character_info['average_item_level'],
                mythic_plus_score=character_info['mythic_plus_score'],
                achievement_points=character_info['achievement_points'],
                vault_slot1_key=character_info['vault_rewards'][0]['key_level'],
                vault_slot1_ilvl=character_info['vault_rewards'][0]['item_level'],
                vault_slot2_key=character_info['vault_rewards'][1]['key_level'],
                vault_slot2_ilvl=character_info['vault_rewards'][1]['item_level'],
                vault_slot3_key=character_info['vault_rewards'][2]['key_level'],
                vault_slot3_ilvl=character_info['vault_rewards'][2]['item_level'],
                raid_slot1_ilvl=character_info['raid_rewards'][0]['item_level'],
                raid_slot2_ilvl=character_info['raid_rewards'][1]['item_level'],
                raid_slot3_ilvl=character_info['raid_rewards'][2]['item_level']
            )
            self.session.add(character)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(f"Insert error: {e}")

    def record_character_snapshot(self, character_info):
        try:
            char_id = character_info['name'] + "-" + character_info['realm']
            snapshot = CharacterSnapshot(
                char_id=char_id,
                name=character_info['name'],
                realm=character_info['realm'],
                guild=character_info.get('guild'),
                level=character_info['level'],
                equipped_item_level=character_info['equipped_item_level'],
                average_item_level=character_info['average_item_level'],
                mythic_plus_score=character_info['mythic_plus_score'],
                achievement_points=character_info['achievement_points'],
                vault_slot1_key=character_info['vault_rewards'][0]['key_level'],
                vault_slot1_ilvl=character_info['vault_rewards'][0]['item_level'],
                vault_slot2_key=character_info['vault_rewards'][1]['key_level'],
                vault_slot2_ilvl=character_info['vault_rewards'][1]['item_level'],
                vault_slot3_key=character_info['vault_rewards'][2]['key_level'],
                vault_slot3_ilvl=character_info['vault_rewards'][2]['item_level'],
                raid_slot1_ilvl=character_info['raid_rewards'][0]['item_level'],
                raid_slot2_ilvl=character_info['raid_rewards'][1]['item_level'],
                raid_slot3_ilvl=character_info['raid_rewards'][2]['item_level'],
                timestamp=datetime.utcnow()
            )
            self.session.add(snapshot)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(f"Snapshot error: {e}")

    def fetch_all_characters(self):
        try:
            characters = self.session.query(CharacterProfile).all()
            result = []
            for character in characters:
                result.append({
                    'char_id': character.char_id,
                    'name': character.name,
                    'realm': character.realm,
                    'guild': character.guild,
                    'level': character.level,
                    'equipped_item_level': character.equipped_item_level,
                    'average_item_level': character.average_item_level,
                    'mythic_plus_score': character.mythic_plus_score,
                    'achievement_points': character.achievement_points,
                    'vault_slot1_key': character.vault_slot1_key,
                    'vault_slot1_ilvl': character.vault_slot1_ilvl,
                    'vault_slot2_key': character.vault_slot2_key,
                    'vault_slot2_ilvl': character.vault_slot2_ilvl,
                    'vault_slot3_key': character.vault_slot3_key,
                    'vault_slot3_ilvl': character.vault_slot3_ilvl,
                    'raid_slot1_ilvl': character.raid_slot1_ilvl,
                    'raid_slot2_ilvl': character.raid_slot2_ilvl,
                    'raid_slot3_ilvl': character.raid_slot3_ilvl
                })
            return result
        except Exception as e:
            self.session.rollback()
            print(f"Fetch error: {e}")
            return []
