import logging
from typing import List

import discord
from discord import app_commands
from discord.ext.commands import GroupCog
from discord.ui import button, View

from exceptions import MessageUnsendable, MessageUnreachable
from features.schedule.constants import YES, THINKING, CANCELLED, NO
from features.schedule.database import ScheduleDB
from features.schedule.display_data import Descriptions, Messages
from features.schedule.models import Event, GuildScheduleConfig
from features.schedule.util import type_autocomplete, guild_registered, author_is_editor, validate_arguments, \
    author_is_admin, parse_date, parse_time, parse_type
from onigiri import Onigiri

desc = Descriptions()
msg = Messages()


@app_commands.guild_only()
class Schedule(GroupCog, name="schedule", description="Commands under the schedule module."):
    def __init__(self, client: Onigiri):
        self.logger = logging.getLogger("onigiri.schedule")
        self.client = client
        self.db = ScheduleDB()
        self.number_of_messages = 2

    async def create_schedule_messages(self, channel: discord.TextChannel) -> List[discord.Message]:
        channel = self.client.get_channel(channel.id)
        messages = []
        for i in range(self.number_of_messages):
            messages.append(await channel.send(content="** **"))
        return messages

    async def update_schedule_messages(self, guild: GuildScheduleConfig) -> None:
        if not self.client.get_guild(guild.guild_id):
            return
        events = await self.db.get_guild_events(guild.guild_id)
        channel = self.client.get_channel(guild.schedule_channel_id)
        if not channel:
            raise MessageUnreachable
        num_messages = len(guild.schedule_message_id_array)
        # TODO

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

        await self.update_schedule_messages(guild)
        await interaction.edit_original_response(content=f"{YES}Done.")

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
        await self.client.update_schedule(interaction.guild.id)


async def setup(client: Onigiri):
    await client.add_cog(Schedule(client))
