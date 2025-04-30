import discord
from discord.ext import commands
from config import DISCORD_TOKEN, DATABASE_URL, DISCORD_GUILD_ID
from libs.sql_handler import SQLHandler

# Command module registrations
from bot_libs.char_commands import register_char_commands
from bot_libs.guild_commands import register_guild_commands
from bot_libs.roster_commands import register_roster_commands
from bot_libs.event_commands import register_event_commands
from bot_libs.reaction_handler import setup_reaction_handler

# Setup DB and bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
db_handler = SQLHandler(DATABASE_URL)
db_handler.create_tables()

setup_reaction_handler(bot, db_handler)

@bot.event
async def on_ready():
    guild = discord.Object(id=DISCORD_GUILD_ID)
    # ⚠️ Befehle in dieser Guild löschen
    #tree.clear_commands(guild=guild)
    #await tree.sync(guild=guild)
    #print(f"🧹 Alle Guild-Commands in {DISCORD_GUILD_ID} gelöscht.")
    
    # Jetzt neu registrieren
    register_char_commands(tree, db_handler, guild=guild)
    register_guild_commands(tree, db_handler, guild=guild)
    register_roster_commands(tree, db_handler, guild=guild)
    register_event_commands(bot, db_handler, guild=guild)
    
    print("📋 Registrierte Slash-Befehle:")
    for cmd in tree.get_commands():
        print(f" - /{cmd.name}")
    
    print("Commands before sync:", tree.get_commands())
    await tree.sync(guild=guild)
    print(f"✅ Bot is online as {bot.user} (commands synced to guild {DISCORD_GUILD_ID})")

if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)