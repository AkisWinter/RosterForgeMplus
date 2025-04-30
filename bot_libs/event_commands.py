import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, UTC
from libs.sql_handler import MythicPlusEvent, MPlusSignup
import json

with open("libs/class_spec_roles.json", "r", encoding="utf-8") as f:
    CLASS_SPEC_ROLE_MAP = json.load(f)

def resolve_role(class_name: str, spec: str) -> str | None:
    return CLASS_SPEC_ROLE_MAP.get(class_name, {}).get(spec)


class SignupModal(discord.ui.Modal, title="Mythic+ Anmeldung"):
    char = discord.ui.TextInput(label="Charaktername (Name-Realm)", required=True)
    spec = discord.ui.TextInput(label="Spec (z. B. Havoc)", required=True)

    def __init__(self, role_wanted: str, event_id: int, db_handler):
        super().__init__()
        self.role_wanted = role_wanted
        self.event_id = event_id
        self.db_handler = db_handler

    async def on_submit(self, interaction: discord.Interaction):
        session = self.db_handler.session
        user_id = str(interaction.user.id)
        char_class = "Demon Hunter"  # ❗ TODO: Aus DB auflösen
        
        resolved_role = resolve_role(char_class, self.spec.value)


        if resolved_role != self.role_wanted:
            await interaction.response.send_message(
                f"❌ Spec '{self.spec.value}' ist keine gültige Rolle für {char_class}. Erwartet: {self.role_wanted}",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"✅ Du hast **{self.char.value}** als **{self.spec.value} ({resolved_role})** für das Event angemeldet.",
            ephemeral=True
        )

class SignupButtonView(discord.ui.View):
    def __init__(self, role: str, event_id: int, db_handler):
        super().__init__(timeout=None)
        self.role = role
        self.event_id = event_id
        self.db_handler = db_handler

    @discord.ui.button(label="Jetzt anmelden", style=discord.ButtonStyle.primary)
    async def signup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SignupModal(
            role_wanted=self.role,
            event_id=self.event_id,
            db_handler=self.db_handler
        ))


def register_event_commands(bot: commands.Bot, db_handler, guild=None):
    tree = bot.tree

    @tree.command(name="create_mplus_event", description="Create a new Mythic+ event", guild=guild)
    @app_commands.describe(name="Name of the event")
    async def create_mplus_event(interaction: discord.Interaction, name: str):
        session = db_handler.session
        user_id = str(interaction.user.id)
        event = MythicPlusEvent(name=name, created_by=user_id, created_at=datetime.now(UTC))
        session.add(event)
        session.commit()

        embed = discord.Embed(title=f"M+ Event: {name}", description="Klicke auf eine Reaktion, um dich anzumelden.", color=discord.Color.blue())
        embed.add_field(name="🛡️ Tank", value="0/1", inline=True)
        embed.add_field(name="💉 Healer", value="0/1", inline=True)
        embed.add_field(name="⚔️ DPS", value="0/3", inline=True)
        embed.set_footer(text="Bot fragt dich nach Charakter & Spec")

        message = await interaction.channel.send(embed=embed)
        await message.add_reaction("🛡️")
        await message.add_reaction("💉")
        await message.add_reaction("⚔️")

        event.message_id = message.id
        session.commit()

        await interaction.response.send_message(f"✅ Event '{name}' erstellt.", ephemeral=True)
        
