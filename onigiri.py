import logging
from typing import Optional

import discord
from discord.ext import commands, tasks

from apis.database_api import OnigiriDB
from tools import *
from tools.constants import LOG_HANDLER


class Onigiri(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        self.db = OnigiriDB()
        self.logger = logging.getLogger("Onigiri")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(LOG_HANDLER)
        super().__init__(command_prefix=commands.when_mentioned_or("$"), intents=intents)

    async def setup_hook(self):
        self.logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        self.logger.info('Starting refresh loop!')
        self.loop_refresh.start()

    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.command:
            self.logger.info("")
            self.logger.info(
                f"<{interaction.user.name}#{interaction.user.discriminator} used "
                f"/{interaction.command.name} in {interaction.guild.name} "
                f"({interaction.guild.id})>")

    async def new_schedule(self, guild_id: int, channel_id: int):
        guild = self.get_guild(guild_id)
        self.logger.info(f"Creating new schedule for guild {guild.name} ({guild.id}).")
        channel = self.get_channel(channel_id)
        message = await channel.send(content=".")
        return message

    async def update_schedule(self, guild_id: int) -> Optional[discord.Message]:
        self.logger.info(f"Updating schedule for guild {guild_id}.")

        guild = self.get_guild(guild_id)
        if not guild:
            self.logger.info(f"    ↳ {guild_id}: This instance is not in the guild.")
            return
        self.logger.info(f"    ↳ {guild_id}: {guild.name}")

        guild = self.db.get_guild(guild_id)
        events = self.db.get_guild_events(guild_id)
        self.logger.info(f"    ↳ {guild_id}: {len(events)} events.")
        channel = self.get_channel(guild.get("schedule_channel_id"))
        if not channel:
            raise discord.NotFound

        message = await channel.fetch_message(guild.get("schedule_message_id"))
        content = render_schedule(guild, events)
        self.logger.info(f"    ↳ {guild_id}: {len(content)} characters.")
        return await message.edit(content=content)

    @tasks.loop(minutes=5)
    async def loop_refresh(self):
        guilds = self.db.get_all_enabled_guilds()
        self.logger.info("")
        self.logger.info(f"<Auto-refreshing all enabled guilds... ({len(guilds)})>")
        for guild in self.db.get_all_enabled_guilds():
            try:
                await self.update_schedule(guild.get("guild_id"))
            except discord.Forbidden:
                self.logger.warning(
                    f"    ↳ {guild.get('guild_id')}: Missing permissions to update message.")
            except discord.NotFound:
                self.logger.warning(
                    f"    ↳ {guild.get('guild_id')}: Schedule message or channel not found.")

    @loop_refresh.before_loop
    async def before_loop(self):
        await self.wait_until_ready()
