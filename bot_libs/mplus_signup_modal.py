import discord
from discord.ext import commands
from discord import app_commands
import json

with open("class_spec_roles.json", "r", encoding="utf-8") as f:
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

        # Beispiel: Klassenzuordnung durch DB oder vorab festgelegt
        # Hier als Platzhalter gesetzt:
        char_class = "Demon Hunter"  # normalerweise über Charakterdatenbank

        resolved_role = resolve_role(char_class, self.spec.value)
        if resolved_role != self.role_wanted:
            await interaction.response.send_message(
                f"❌ Spec '{self.spec.value}' ist keine gültige Rolle für {char_class}. Erwartet: {self.role_wanted}",
                ephemeral=True
            )
            return

        # Optional: In MPlusSignup eintragen
        # session.add(MPlusSignup(...))
        # session.commit()

        await interaction.response.send_message(
            f"✅ Du hast **{self.char.value}** als **{self.spec.value} ({resolved_role})** für das Event angemeldet.",
            ephemeral=True
        )

# Beispiel: Verwendung des Modals nach Reaktion oder Command
# await interaction.response.send_modal(SignupModal(role_wanted="Tank", event_id=123, db_handler=db_handler))