from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
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
    class_name = Column(String(50))
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
    class_name = Column(String(50))
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

class TrackedGuild(Base):
    __tablename__ = 'tracked_guilds'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    realm = Column(String, nullable=False)

class UserCharacter(Base):
    __tablename__ = 'user_characters'

    id = Column(Integer, primary_key=True)
    discord_id = Column(String, nullable=False)
    character_id = Column(String, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

class Rooster(Base):
    __tablename__ = 'roosters'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    members = relationship("RoosterMember", back_populates="rooster")

class RoosterMember(Base):
    __tablename__ = 'rooster_members'

    id = Column(Integer, primary_key=True)
    rooster_id = Column(Integer, ForeignKey('roosters.id'))
    character_id = Column(String, nullable=False)
    rooster = relationship("Rooster", back_populates="members")

class SQLHandler:
    def __init__(self, database_url):
        self.database_url = database_url
        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def create_tables(self):
        Base.metadata.create_all(self.engine)
        # Optionally insert default tracked guilds
        default_guilds = [
            #{"name": "Requiem DSH", "realm": "Antonidas"}
        ]
        for g in default_guilds:
            if not self.session.query(TrackedGuild).filter_by(name=g["name"], realm=g["realm"]).first():
                self.session.add(TrackedGuild(name=g["name"], realm=g["realm"]))
        self.session.commit()
        print("Tables created successfully.")

    def insert_character_info(self, character_info):
        try:
            char_id = character_info['name'] + "-" + character_info['realm']
            char_id = char_id.replace(" ", "").replace("'", "")
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
            char_id = char_id.replace(" ", "").replace("'", "")
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


    def add_tracked_guild(self, name, realm):
        try:
            existing = self.session.query(TrackedGuild).filter_by(name=name, realm=realm).first()
            if existing:
                return False
            self.session.add(TrackedGuild(name=name, realm=realm))
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error adding tracked guild: {e}")
            return False
    
    def remove_tracked_guild(self, name, realm):
        try:
            deleted = self.session.query(TrackedGuild).filter_by(name=name, realm=realm).delete()
            self.session.commit()
            return deleted > 0
        except Exception as e:
            self.session.rollback()
            print(f"Error removing tracked guild: {e}")
            return False
