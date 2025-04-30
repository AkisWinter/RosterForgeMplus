# 🛡️ WoW Guildanalyser Discord Bot

Ein leistungsstarker Discord-Bot zur Verwaltung, Auswertung und Darstellung von WoW-Charakterprofilen, Raid-Roostern und Gildenverfolgung. Unterstützt Blizzard API und optional Raider.IO für Mythic+ Daten.

---

## 🔧 Features

- `/add_char` – Charakter verlinken & Profil sofort abrufen
- `/remove_char` – Charakterverlinkung aufheben
- `/list_chars` – Verlinkte Charaktere übersichtlich anzeigen (inkl. Vault & Score)
- `/add_guild` – Gilde zur Überwachung hinzufügen
- `/remove_guild` – Gilde entfernen
- `/list_guilds` – Alle getrackten Gilden anzeigen
- `/create_rooster` – Raid-Rooster anlegen
- `/delete_rooster` – Rooster löschen
- `/add_to_rooster` – Charakter zum Rooster hinzufügen (inkl. Profilabruf)
- `/remove_from_rooster` – Charakter aus Rooster entfernen
- `/list_rooster_members` – Mitglieder eines Roosters mit vollständiger Darstellung
- `/list_roosters` – Übersicht aller Rooster
- `/roosters_invites` – List /inv lines for all members of a rooster

---

## 🚀 Setup

### Voraussetzungen

- Python 3.10+
- Discord Bot Token
- Blizzard API Credentials
- (optional) Raider.IO API Token

### Installation

```bash
git clone https://github.com/dein-repo/wow-guildanalyser-bot.git
cd wow-guildanalyser-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
