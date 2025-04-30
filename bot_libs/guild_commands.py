### File: guild_commands.py

import discord
from discord import app_commands
from libs.sql_handler import TrackedGuild

def register_guild_commands(tree: discord.app_commands.CommandTree, db_handler, guild=None):

    @tree.command(name="add_guild", description="Add a guild to tracking list")
    @app_commands.describe(name="Guild name", realm="Guild realm")
    async def add_guild(interaction: discord.Interaction, name: str, realm: str):
        session = db_handler.session
        try:
            exists = session.query(TrackedGuild).filter_by(name=name, realm=realm).first()
            if exists:
                await interaction.response.send_message(f"Guild '{name}' on '{realm}' is already tracked.", ephemeral=True)
                return

            session.add(TrackedGuild(name=name, realm=realm))
            session.commit()
            await interaction.response.send_message(f"✅ Guild '{name}' on realm '{realm}' added to tracking.", ephemeral=True)
        except Exception as e:
            session.rollback()
            await interaction.response.send_message(f"❌ Failed to add guild: {e}", ephemeral=True)

    @tree.command(name="remove_guild", description="Remove a tracked guild")
    @app_commands.describe(name="Guild name", realm="Guild realm")
    async def remove_guild(interaction: discord.Interaction, name: str, realm: str):
        session = db_handler.session
        try:
            deleted = session.query(TrackedGuild).filter_by(name=name, realm=realm).delete()
            session.commit()
            if deleted:
                await interaction.response.send_message(f"✅ Guild '{name}' on realm '{realm}' removed.", ephemeral=True)
            else:
                await interaction.response.send_message(f"Guild '{name}' on realm '{realm}' not found.", ephemeral=True)
        except Exception as e:
            session.rollback()
            await interaction.response.send_message(f"❌ Failed to remove guild: {e}", ephemeral=True)

    @tree.command(name="list_guilds", description="List all tracked guilds")
    async def list_guilds(interaction: discord.Interaction):
        session = db_handler.session
        try:
            guilds = session.query(TrackedGuild).all()
            if not guilds:
                await interaction.response.send_message("No guilds are being tracked.", ephemeral=True)
                return

            lines = [f"{g.name} - {g.realm}" for g in guilds]
            msg = "```\n" + "\n".join(lines) + "\n```"
            await interaction.response.send_message(msg, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to list guilds: {e}", ephemeral=True)
