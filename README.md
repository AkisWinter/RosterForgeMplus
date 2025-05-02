# RosterForMplus

---

## 🔧 Features

- `/add_char` – Link character & fetch profile immediately  
- `/remove_char` – Unlink character  
- `/list_chars` – Display linked characters clearly (including Vault & Score)  
- `/add_guild` – Add guild for monitoring  
- `/remove_guild` – Remove guild  
- `/list_guilds` – Show all tracked guilds  
- `/create_roster` – Create a raid roster  
- `/delete_roster` – Delete a roster  
- `/add_to_roster` – Add character to roster (including profile fetch)  
- `/remove_from_roster` – Remove character from roster  
- `/list_roster_members` – Show roster members with full details  
- `/list_rosters` – Overview of all rosters  
- `/rosters_invites` – List /inv lines for all members of a roster

---

## 🚀 Setup

### Requirements

- Python 3.10+
- Discord Bot Token
- Blizzard API Credentials
- (optional) Raider.IO API Token

### Installation

```bash
git clone https://github.com/AkisWinter/RosterForMplus.git
cd RosterForMplus
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

.env example:

```Text
# Discord settings
DISCORD_TOKEN=
DISCORD_GUILD_ID=

# Raider io API
RAIDERIO_ACCESS_KEY=
USE_RAIDERIO_FOR_MPLUS=True
# True = Raider.IO, False = Blizzard API

# Blizzard API
CLIENT_ID=
CLIENT_SECRET=

# Blizzard API Settings
REGION=eu
REALM_SLUG=destromath
GUILD_NAME=einsamer-worg
LOCALE=en_GB

# Database Settings
DB_TYPE=sqlite
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=password
DB_NAME=wowdata
```

