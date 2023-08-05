import logging
from typing import List

import discord
from discord import app_commands
from discord.ext import tasks
from discord.ext.commands import GroupCog
from discord.ui import button, View

from exceptions import MessageUnsendable, MessageUnreachable
from features.schedule.constants import YES, THINKING, CANCELLED, NO
from features.schedule.database import ScheduleDB
from features.schedule.display_data import Descriptions, Messages
from features.schedule.models import Event, GuildScheduleConfig
from features.schedule.util import type_autocomplete, guild_registered, author_is_editor, validate_arguments, \
    author_is_admin, parse_date, parse_time, parse_type, render_schedule
from onigiri import Onigiri

desc = Descriptions()
msg = Messages()


def split_messages(schedule_content: List[str], num_messages: int) -> List[List[str]]:
    total_length = sum(len(s) for s in schedule_content)
    target_length = total_length // num_messages
    sub_lists = [[]]
    current_length = 0
    for line in schedule_content:
        if len(sub_lists) == num_messages:
            sub_lists[-1].append(line)
            continue
        new_length = current_length + len(line)
        if abs(target_length - new_length) <= abs(target_length - current_length):
            sub_lists[-1].append(line)
            current_length = new_length
        else:
            sub_lists.append([line])
            current_length = len(line)
    while len(sub_lists) < num_messages:
        sub_lists.append([' '])
    return sub_lists


@app_commands.guild_only()
class Schedule(GroupCog, name="schedule", description="Commands under the schedule module."):
    def __init__(self, client: Onigiri):
        self.logger = logging.getLogger("Onigiri.schedule")
        self.client = client
        self.db = ScheduleDB()
        self.number_of_messages = 2
        self.update_schedule.start()

    def cog_unload(self) -> None:
        self.update_schedule.cancel()

    async def create_schedule_messages(self, channel: discord.TextChannel) -> List[discord.Message]:
        channel = self.client.get_channel(channel.id)
        messages = []
        for i in range(self.number_of_messages):
            messages.append(await channel.send(content="** **"))
        return messages

    async def update_schedule_messages(self, guild_id: int) -> None:
        self.logger.info(f"Updating schedule for guild {guild_id}:")
        log_prefix = f"    ↳ {guild_id}: "
        discord_guild = self.client.get_guild(guild_id)
        if not discord_guild:
            self.logger.info(f"{log_prefix}This bot instance is not in the guild.")
            return
        guild = await self.db.get_guild(guild_id)
        if not guild:
            self.logger.warning(f"{log_prefix}Guild is not registered!")
            return
        self.logger.info(f"{log_prefix}{discord_guild.name}")
        events = await self.db.get_guild_events(guild.guild_id)
        self.logger.info(f"{log_prefix}{len(events)} events.")
        channel = self.client.get_channel(guild.schedule_channel_id)
        if not channel:
            raise MessageUnreachable
        num_messages = len(guild.schedule_message_id_array)
        schedule = render_schedule(guild, events)
        schedule_messages = split_messages(schedule, num_messages)
        total_length = 0
        for i, message_id in enumerate(guild.schedule_message_id_array):
            message = await channel.fetch_message(message_id)
            if not schedule_messages[i][-1]:
                schedule_messages[i][-1] = "** **"
            if not schedule_messages[i][0]:
                schedule_messages[i][0] = "** **"
            if schedule_messages[i][0].startswith(" "):
                schedule_messages[i][0] = "** **" + schedule_messages[i][0][1:]
            content = "\n".join(schedule_messages[i])
            total_length += len(content)
            self.logger.info(f"{log_prefix}Message {i}, {len(content)} characters.")
            await message.edit(content=content)
        self.logger.info(f"{log_prefix}Total {total_length} characters.")

    @tasks.loop(minutes=2)
    async def update_schedule(self):
        guilds = await self.db.get_enabled_guilds()
        self.logger.info(f"<Auto-refreshing all enabled guilds... ({len(guilds)})>")
        for guild in guilds:
            log_prefix = f"    ↳ {guild.guild_id}: "
            try:
                await self.update_schedule_messages(guild.guild_id)
            except discord.Forbidden:
                self.logger.warning(f"{log_prefix}Missing permissions to update message.")
            except discord.NotFound:
                self.logger.warning(f"{log_prefix}Schedule message or channel not found.")
            except Exception as e:
                self.logger.exception(e)

    @update_schedule.before_loop
    async def before_update_schedule(self):
        await self.client.wait_until_ready()

    # ===============
    # /schedule setup
    # ===============
    @app_commands.command(name="setup", description=desc.cmd_setup)
    @app_commands.describe(channel=desc.schedule_channel)
    @app_commands.default_permissions(manage_guild=True)
    @author_is_admin()
    async def setup_guild(self, interaction: discord.Interaction, channel: discord.TextChannel):
        class OverrideView(View):
            def __init__(self):
                super().__init__(timeout=120)
                self.confirm = None

            @button(label='Confirm', style=discord.ButtonStyle.blurple)
            async def confirm(self, *_):
                self.confirm = True
                self.stop()

            @button(label='Cancel', style=discord.ButtonStyle.secondary)
            async def cancel(self, *_):
                self.confirm = False
                self.stop()

        guild = await self.db.get_guild(interaction.guild.id)

        # Confirmation for overriding schedule channel
        if guild and guild.schedule_channel_id:
            view = OverrideView()
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(
                msg.setup_override.format(channel=channel.mention), view=view, ephemeral=True
            )
            timeout = await view.wait()
            if not timeout:
                if view.confirm:
                    await interaction.edit_original_response(content=f"{THINKING}**Setting up...**", view=None)
                else:
                    return await interaction.edit_original_response(content=f"{CANCELLED}**Cancelled.**", view=None)
            else:
                return await interaction.edit_original_response(content=f"{NO}**Response timed out.**", view=None)
        else:
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{THINKING}**Setting up...**", ephemeral=True)

        # Create messages
        try:
            messages = await self.create_schedule_messages(channel)
        except discord.Forbidden:
            raise MessageUnsendable
        assert messages

        # Update / create guild in DB
        if guild:
            guild.schedule_message_id_array = [message.id for message in messages]
            await self.db.update_guild(guild)
        else:
            guild = GuildScheduleConfig(
                guild_id=interaction.guild.id,
                schedule_channel_id=interaction.channel.id,
                schedule_message_id_array=[message.id for message in messages],
                editor_role_id_array=[]
            )
            await self.db.create_guild(guild)

        await self.update_schedule_messages(guild.guild_id)
        await interaction.edit_original_response(content=f"{YES}Done.")

    # =============
    # /schedule add
    # =============
    @app_commands.command(name="add", description=desc.cmd_add)
    @app_commands.describe(
        title=desc.title, event_type=desc.event_type, url=desc.url, date=desc.date, time=desc.time, note=desc.note
    )
    @app_commands.rename(event_type="type")
    @app_commands.autocomplete(event_type=type_autocomplete)
    @app_commands.default_permissions(send_messages=True)
    @guild_registered()
    @author_is_editor()
    @validate_arguments
    async def add_event(
            self, interaction: discord.Interaction,
            title: str,
            url: str = "",
            date: str = "",
            time: str = "",
            note: str = "",
            event_type: str = 'stream',
    ) -> None:
        datetime, granularity = parse_date(date)
        if datetime:
            datetime = parse_time(time, datetime)
        event = Event(
            guild_id=interaction.guild.id,
            event_id=await self.db.get_available_event_id(interaction.guild.id),
            title=title,
            datetime=datetime,
            datetime_granularity=granularity,
            type=parse_type(event_type),
            note=note,
            url=url
        )
        await self.db.create_event(event)
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(f"{YES}**Event `{event.event_id}` created.**", ephemeral=True)
        await self.update_schedule_messages(interaction.guild.id)

    # =================
    # /schedule refresh
    # =================
    @app_commands.command(name="refresh", description=desc.cmd_refresh)
    @app_commands.default_permissions(send_messages=True)
    @guild_registered()
    @author_is_editor()
    async def refresh_schedule(self, interaction: discord.Interaction):
        # noinspection PyUnresolvedReferences
        await interaction.response.defer(ephemeral=True)
        await self.update_schedule_messages(interaction.guild.id)
        await interaction.followup.send(content=f"{YES}**Schedule refreshed.**")


async def setup(client: Onigiri):
    await client.add_cog(Schedule(client))
