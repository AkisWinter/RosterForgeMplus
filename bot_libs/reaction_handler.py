import discord
from discord.ext import commands
from bot_libs.event_commands import SignupButtonView
from libs.sql_handler import MythicPlusEvent

EMOJI_ROLE_MAP = {
    "🛡️": "Tank",
    "💉": "Healer",
    "⚔️": "DPS"
}

def setup_reaction_handler(bot: commands.Bot, db_handler):
    @bot.event
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
        if payload.user_id == bot.user.id:
            return

        emoji = payload.emoji.name
        if emoji not in EMOJI_ROLE_MAP:
            return

        role = EMOJI_ROLE_MAP[emoji]

        # Event nach message_id finden
        session = db_handler.session
        event = session.query(MythicPlusEvent).filter_by(message_id=payload.message_id).first()
        if not event:
            return

        # Channel und Member laden
        channel = await bot.fetch_channel(payload.channel_id)
        member = payload.member or await channel.guild.fetch_member(payload.user_id)

        # Nachricht privat oder als Followup senden
        try:
            view = SignupButtonView(role=role, event_id=event.id, db_handler=db_handler)
            await member.send(
                f"📥 Du möchtest dich für **{role}** im Event **{event.name}** anmelden.",
                view=view
            )
        except discord.Forbidden:
            await channel.send(f"{member.mention}, ich konnte dir keine DM schicken. Bitte prüfe deine Privatsphäre-Einstellungen.")