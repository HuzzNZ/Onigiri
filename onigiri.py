import logging
from typing import Optional, List

import discord
from discord.ext import commands, tasks
from numpy import array_split

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
        self.ofs_auto_role_guild_id = 679651751753941002
        self.ofs_auto_role_role_id = 679653891595304985
        self.ofs_auto_role_status = self.db.get_auto_role_status(self.ofs_auto_role_guild_id)
        self.test_auto_role_status = self.db.get_auto_role_status(547571343986524180)
        super().__init__(command_prefix=commands.when_mentioned_or("$"), intents=intents)

    async def setup_hook(self):
        self.logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        self.logger.info('Starting refresh loop!')
        self.loop_refresh.start()

    async def on_member_join(self, member: discord.Member):
        self.logger.info(f'<{member.name} has joined {member.guild.name} ({member.guild.id}), '
                         f'pending = {member.pending}>')

    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.command:
            self.logger.info("")
            self.logger.info(
                f"<{interaction.user.name} used "
                f"/{interaction.command.name} in {interaction.guild.name} "
                f"({interaction.guild.id}).>")

    async def on_member_update(self, before: discord.Member, m: discord.Member):
        if not before.guild.id == self.ofs_auto_role_guild_id:
            return
        if self.ofs_auto_role_status and before.pending and not m.pending:
            self.logger.info(f'<{m.name} has been verified in {m.guild.name} ({m.guild.id}).>')
            await m.add_roles(self.get_guild(self.ofs_auto_role_guild_id).get_role(self.ofs_auto_role_role_id))
            self.logger.info("")
            self.logger.info(
                f"<User {m.id} ({m.name}) completed verification and was assigned a role in "
                f"{self.get_guild(self.ofs_auto_role_guild_id).name} ({self.ofs_auto_role_guild_id}).>"
            )

    async def new_schedule(self, guild_id: int, channel_id: int) -> [discord.Message]:
        guild = self.get_guild(guild_id)
        self.logger.info(f"Creating new schedule for guild {guild.name} ({guild.id}).")
        channel = self.get_channel(channel_id)
        messages = []
        for i in range(2):
            messages.append(await channel.send(content="** **"))
        self.db.add_or_edit_guild(
            guild_id,
            channel_id,
            [m.id for m in messages]
        )
        return messages

    async def update_schedule(self, guild_id: int) -> Optional[List[discord.Message]]:
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

        message_ids = guild.get("schedule_message_ids")
        render_past = True
        if not message_ids:
            message_ids = [guild.get("schedule_message_id")]
            self.logger.info(f"    ↳ {guild_id}: Guild not yet migrated!")
            render_past = False

        messages = len(message_ids)
        contents = render_schedule(guild, events, render_past)
        message_contents = [list(x) for x in array_split(contents, messages)]
        return_messages = []
        total_length = 0

        for i in range(len(message_ids)):
            msg = await channel.fetch_message(message_ids[i])

            # Pad whitespace
            if not message_contents[i][-1]:
                message_contents[i][-1] = "** **"
            if not message_contents[i][0]:
                message_contents[i][0] = "** **"
            if message_contents[i][0].startswith(" "):
                message_contents[i][0] = "** **" + message_contents[i][0][1:]

            content = "\n".join(message_contents[i])
            message = await msg.edit(content=content)
            total_length += len(content)
            self.logger.info(f"    ↳ {guild_id}: Message {i + 1}, {len(content)} characters.")
            return_messages.append(message)
        self.logger.info(f"    ↳ {guild_id}: Total {total_length} characters.")
        return return_messages

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
