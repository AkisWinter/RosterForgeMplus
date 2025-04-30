import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Discord Settings
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))

# Raider.IO Settings
USE_RAIDERIO_FOR_MPLUS = os.getenv("USE_RAIDERIO_FOR_MPLUS", "true").lower() == "true"
RAIDERIO_ACCESS_KEY = os.getenv("RAIDERIO_ACCESS_KEY")


# Blizzard API Settings
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REGION = os.getenv("REGION", "eu")
REALM_SLUG = os.getenv("REALM_SLUG")
GUILD_NAME = os.getenv("GUILD_NAME")
LOCALE = os.getenv("LOCALE", "en_GB")

# Database Settings
DB_TYPE = os.getenv("DB_TYPE", "sqlite")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "wowdata")

# Compose DATABASE_URL
if DB_TYPE == "sqlite":
    DATABASE_URL = f"sqlite:///./{DB_NAME}.db"
elif DB_TYPE == "mysql":
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
elif DB_TYPE == "postgresql":
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    raise ValueError(f"Unsupported DB_TYPE: {DB_TYPE}")

# Mythic Plus Reward Mapping
MYTHIC_PLUS_MAPPING = {
    10: 662,
    9: 658,
    7: 658,
    6: 655,
    4: 652,
    2: 649,
    0: 645
}

# Raid Reward Mapping
RAID_MAPPING = {
    "LFR": 623,
    "Normal": 636,
    "Heroic": 649,
    "Mythic": 662
}

# Active Raid Settings
ACTIVE_RAID_NAME = "Liberation of Undermine"
ACTIVE_RAID_DIFFICULTY = "Heroic"


