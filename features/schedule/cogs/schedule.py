import discord
from discord import app_commands
from discord.ext.commands import GroupCog
from discord.ui import button, View

from features.metadata import features
from features.schedule.database import ScheduleDB
from features.schedule.models import Event
from features.schedule.util import type_autocomplete, guild_registered, author_is_editor, validate_arguments, \
    author_is_admin, parse_date, parse_time, parse_type

from onigiri import Onigiri
from tools.constants import YES, THINKING, CANCELLED, NO, WARNING

DESC_PREFIX = features['schedule']['desc_prefix']


@app_commands.guild_only()
class Schedule(GroupCog, group_name="schedule"):
    def __init__(self, client: Onigiri):
        self.client = client
        self.db = ScheduleDB()

    @app_commands.command(
        name="setup",
        description=DESC_PREFIX + "Setup command. Sets the schedule channel and creates a new set of schedule messages."
    )
    @app_commands.describe(
        channel="The channel to host the schedule messages."
    )
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
            await interaction.response.send_message(
                f"{WARNING}**You are currently overriding the schedule channel.** "
                f"This will create new schedule messages in {channel.mention}, "
                "and render the current schedule messages static (can be safely deleted).",
                view=view, ephemeral=True
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
            await interaction.response.send_message(f"{THINKING}**Setting up...**", ephemeral=True)

        try:
            ...  # create_messages()
        except discord.Forbidden:
            ...  # err

        if guild:
            ...  # update guild
        else:
            ...  # create guild

        try:
            ...  # update messages
        except (discord.Forbidden, discord.NotFound):
            ...  # err
        await interaction.edit_original_response(content=f"{YES}Done.")

    @app_commands.command(
        name="add",
        description=DESC_PREFIX + "Adds an event to the schedule."
    )
    @app_commands.describe(
        title="The title of the event. Max 30 characters. Try to keep it short and concise!",
        event_type="The type of the event. Defaults to stream.",
        url="The URL/Link of an event. (YouTube URLs can be recognized)",
        date="The date of the event in JST. (e.g. Jul 12, 22/7/12, 7/12, 12 Jul 2022, October, 2023, today, tomorrow, "
             "etc.)",
        time="The time of the event in JST. (e.g. 8:00 pm, 20:00, 20, 3am, 27:00, now, etc.)",
        note="A note to go with the event."
    )
    @app_commands.rename(
        event_type="type"
    )
    @app_commands.autocomplete(
        event_type=type_autocomplete
    )
    @guild_registered()
    @author_is_editor()
    @validate_arguments
    async def add_event(
            self,
            interaction: discord.Interaction,
            title: str,
            url: str = "",
            date: str = "",
            time: str = "",
            note: str = "",
            event_type: str = 'stream',
    ) -> None:
        datetime = None
        date, granularity = parse_date(date)
        if date:
            datetime = parse_time(time, date)
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
        await interaction.response.send_message(f"{YES}**Event `{event.event_id}` created.**", ephemeral=True)
        await self.client.update_schedule(interaction.guild.id)


async def setup(client: Onigiri):
    await client.add_cog(Schedule(client))
