from typing import Optional

import discord
from discord.ext import commands, tasks

from apis.database_api import OnigiriDB
from tools import *


class Onigiri(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        self.db = OnigiriDB()
        super().__init__(command_prefix=commands.when_mentioned_or("$"), intents=intents)

    async def setup_hook(self):
        print(f'{log_time()}Logged in as {self.user} (ID: {self.user.id})')
        print(f'{log_time()}Starting refresh loop!')
        self.loop_refresh.start()

    async def new_schedule(self, guild_id: int, channel_id: int):
        guild = self.get_guild(guild_id)
        print(f"{log_time()}Creating new schedule for guild {guild.name} ({guild.id}).")
        channel = self.get_channel(channel_id)
        message = await channel.send(content=".")
        return message

    async def update_schedule(self, guild_id: int) -> Optional[discord.Message]:
        print(f"{log_time()}Updating schedule for guild {guild_id}.")

        guild = self.get_guild(guild_id)
        if not guild:
            print(f"{log_time()}    ↳ {guild_id}: This instance is not in the guild.")
            print(f"{log_time()}")
            return
        print(f"{log_time()}    ↳ {guild_id}: {guild.name}")

        guild = self.db.get_guild(guild_id)
        events = self.db.get_guild_events(guild_id)
        channel = self.get_channel(guild.get("schedule_channel_id"))
        if not channel:
            raise discord.NotFound

        message = await channel.fetch_message(guild.get("schedule_message_id"))
        content = render_schedule(guild, events)
        print(f"{log_time()}    ↳ {guild_id}: Message length currently {len(content)}")
        print(f"{log_time()}")
        return await message.edit(content=content)

    @tasks.loop(minutes=5)
    async def loop_refresh(self):
        for guild in self.db.get_all_enabled_guilds():
            try:
                await self.update_schedule(guild.get("guild_id"))
            except discord.Forbidden:
                print(f"{log_time()}    "
                      f"↳ {guild.get('guild_id')}: Missing permissions to update message.")
                print(f"{log_time()}")
            except discord.NotFound:
                print(f"{log_time()}    "
                      f"↳ {guild.get('guild_id')}: Schedule message or channel not found.")
                print(f"{log_time()}")

    @loop_refresh.before_loop
    async def before_loop(self):
        await self.wait_until_ready()
