import logging
from typing import List

import discord
from discord import app_commands, NotFound, Forbidden
from discord.ext import tasks
from discord.ext.commands import GroupCog
from discord.ui import button, View

from exceptions import InvalidArgument
from features.schedule.exceptions import MessageUnsendable, MessageUnreachable
from features.schedule.constants import YES, THINKING, CANCELLED, NO, WARNING
from features.schedule.database import ScheduleDB
from features.schedule.display_data import Descriptions, Messages
from features.schedule.models import Event, GuildScheduleConfig, DatetimeGranularity
from features.schedule.util import type_autocomplete, guild_registered, author_is_editor, validate_arguments, \
    author_is_admin, parse_date, parse_time, parse_type, render_schedule, guild_enabled
from onigiri import Onigiri

desc = Descriptions()
msg = Messages()
event_descriptions = {
    "title": desc.title,
    "event_type": desc.event_type,
    "url": desc.url,
    "date": desc.date,
    "time": desc.time,
    "note": desc.note
}


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
@app_commands.default_permissions(send_messages=True)
class Schedule(GroupCog, name="schedule", description="Commands under the schedule module."):
    def __init__(self, client: Onigiri):
        super().__init__()
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
            try:
                message = await channel.fetch_message(message_id)
            except NotFound:
                raise MessageUnreachable
            except Forbidden:
                raise MessageUnreachable
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
            except MessageUnreachable:
                self.logger.warning(f"{log_prefix}Schedule message(s) unreachable.")
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
                return await interaction.edit_original_response(content=f"{CANCELLED}**Timed out.**", view=None)
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

    # ============================
    # /schedule config SUBCOMMANDS
    # ============================
    @app_commands.default_permissions(send_messages=True)
    class Config(app_commands.Group):
        def __init__(self, parent_cog):
            super().__init__(description="A description")
            self.db = ScheduleDB()
            self.parent_cog: Schedule = parent_cog

        @app_commands.command(description=desc.cmd_config_status)
        @guild_registered()
        @author_is_admin()
        async def status(self, interaction: discord.Interaction):
            guild = await self.db.get_guild(interaction.guild.id)
            # TODO: Nicer formatting
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{guild}", ephemeral=True)

        @app_commands.command(description=desc.cmd_config_enable)
        @guild_registered()
        @author_is_admin()
        async def enable(self, interaction: discord.Interaction):
            await self.db.set_guild_enable(interaction.guild.id)
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(
                f"{YES}The **Schedule** feature has been **enabled** for this server.", ephemeral=True
            )
            await self.parent_cog.update_schedule_messages(interaction.guild.id)

        @app_commands.command(description=desc.cmd_config_disable)
        @guild_registered()
        @guild_enabled()
        @author_is_admin()
        async def disable(self, interaction: discord.Interaction):
            await self.db.set_guild_disable(interaction.guild.id)
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(
                f"{YES}The **Schedule** feature has been **disabled** for this server.", ephemeral=True
            )
            await self.parent_cog.update_schedule_messages(interaction.guild.id)

        @app_commands.command(name="description", description=desc.cmd_config_desc)
        @app_commands.describe(description=desc.description)
        @guild_registered()
        @guild_enabled()
        @author_is_admin()
        @validate_arguments
        async def description_(self, interaction: discord.Interaction, description: str = ""):
            if len(description) > 200:
                raise InvalidArgument(
                    f"Schedule description must be less than 200 characters (currently {len(description)})."
                )
            await self.db.set_guild_description(interaction.guild.id, description)
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(
                (f"{YES}The **description** of the schedule has been updated to:"
                 f"\n\n> {description}" if description else
                 f"{YES}The **description** of the schedule has been reset."), ephemeral=True
            )
            await self.parent_cog.update_schedule_messages(interaction.guild.id)

        @app_commands.command(description=desc.cmd_config_talent)
        @app_commands.describe(talent=desc.talent)
        @guild_registered()
        @guild_enabled()
        @author_is_admin()
        @validate_arguments
        async def talent(self, interaction: discord.Interaction, talent: str = ""):
            if len(talent) > 30:
                raise InvalidArgument(
                    f"The name of the schedule's talent must be less than 30 characters (currently {len(talent)})."
                )
            await self.db.set_guild_talent(interaction.guild.id, talent)
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(
                (f"{YES}The **talent** of the schedule has been updated to:\n\n> {talent}" if talent else
                 f"{YES}The **talent** of the schedule has been reset."), ephemeral=True
            )
            await self.parent_cog.update_schedule_messages(interaction.guild.id)

        @app_commands.command(description=desc.cmd_config_editor)
        @app_commands.describe(editor=desc.editor_role)
        @app_commands.rename(editor="role")
        @guild_registered()
        @guild_enabled()
        @author_is_admin()
        async def editor(self, interaction: discord.Interaction, editor: discord.Role = None):
            if editor:
                await self.db.set_guild_editors(interaction.guild.id, [editor.id])
            else:
                await self.db.set_guild_editors(interaction.guild.id, [])
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(
                (f"{YES}The **schedule editor role** has been set to **{editor.mention}**." if editor else
                 f"{YES}The **schedule editor role** has been reset."), ephemeral=True
            )

        @app_commands.command(name="reset-all", description=desc.cmd_config_reset_all)
        @guild_registered()
        @author_is_admin()
        async def reset_all(self, interaction: discord.Interaction):
            # TODO
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{NO}**Not implemented yet.**", ephemeral=True)

        @app_commands.command(name="reset-config", description=desc.cmd_config_reset_config)
        @guild_registered()
        @author_is_admin()
        async def reset_config(self, interaction: discord.Interaction):
            # TODO
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{NO}**Not implemented yet.**", ephemeral=True)

        @app_commands.command(name="reset-events", description=desc.cmd_config_reset_events)
        @guild_registered()
        @author_is_admin()
        async def reset_events(self, interaction: discord.Interaction):
            # TODO
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{NO}**Not implemented yet.**", ephemeral=True)

    # =============
    # /schedule add
    # =============
    @app_commands.command(name="add", description=desc.cmd_add)
    @app_commands.describe(**event_descriptions)
    @app_commands.rename(event_type="type")
    @app_commands.autocomplete(event_type=type_autocomplete)
    @app_commands.default_permissions(send_messages=True)
    @guild_registered()
    @guild_enabled()
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

    # ==============
    # /schedule edit
    # ==============
    @app_commands.command(name="edit", description=desc.cmd_edit)
    @app_commands.describe(**event_descriptions, event_id=desc.event_id)
    @app_commands.rename(event_type="type", event_id="id")
    @app_commands.autocomplete(event_type=type_autocomplete)
    @app_commands.default_permissions(send_messages=True)
    @guild_registered()
    @guild_enabled()
    @author_is_editor()
    @validate_arguments
    async def edit_event(
            self, interaction: discord.Interaction, event_id: str,
            title: str = "",
            url: str = "",
            date: str = "",
            time: str = "",
            note: str = "",
            event_type: str = "",
    ) -> None:
        event = await self.db.get_event(interaction.guild.id, event_id)
        datetime = None
        granularity = None
        if date:
            datetime, granularity = parse_date(date)
            if datetime:
                datetime = parse_time(time, datetime)
        if event_type:
            event_type = parse_type(event_type)
        await self.db.update_event(Event(
            guild_id=interaction.guild.id,
            event_id=event.event_id,
            title=title or event.title,
            datetime=datetime or event.datetime,
            datetime_granularity=granularity or event.datetime_granularity,
            type=event_type or event.type,
            note=note or event.note,
            url=url or event.url
        ))
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(f"{YES}**Event `{event_id}` updated**.", ephemeral=True)
        await self.update_schedule_messages(interaction.guild.id)

    # ================
    # /schedule delete
    # ================
    @app_commands.command(name="delete", description=desc.cmd_delete)
    @app_commands.describe(event_id=desc.event_id)
    @app_commands.rename(event_id="id")
    @app_commands.default_permissions(send_messages=True)
    @guild_registered()
    @guild_enabled()
    @author_is_editor()
    @validate_arguments
    async def delete_event(self, interaction: discord.Interaction, event_id: str):
        class DeleteConfirmation(View):
            def __init__(self):
                super().__init__(timeout=120)
                self.delete = None

            @button(label='Delete', style=discord.ButtonStyle.red)
            async def delete(self, *_):
                self.delete = True
                self.stop()

            @button(label='Cancel', style=discord.ButtonStyle.secondary)
            async def cancel(self, *_):
                self.delete = False
                self.stop()
        view = DeleteConfirmation()
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(
            f"{WARNING}**Are you sure you want to delete event `{event_id}`?**\n"
            f"If the event was cancelled, consider using **/schedule stash id:`{event_id}`**.",
            view=view, ephemeral=True
        )
        timeout = await view.wait()
        if not timeout:
            if view.delete:
                await self.db.delete_event(interaction.guild.id, event_id)
                await interaction.edit_original_response(content=f"{YES}**Event `{event_id}` deleted.**", view=None)
                await self.update_schedule_messages(interaction.guild.id)
            else:
                await interaction.edit_original_response(content=f"{CANCELLED}**Cancelled.**", view=None)
        else:
            await interaction.edit_original_response(content=f"{CANCELLED}**Timed out.**", view=None)

    # ===============
    # /schedule stash
    # ===============
    @app_commands.command(name="stash", description=desc.cmd_stash)
    @app_commands.describe(event_id=desc.event_id)
    @app_commands.rename(event_id="id")
    @app_commands.default_permissions(send_messages=True)
    @guild_registered()
    @guild_enabled()
    @author_is_editor()
    @validate_arguments
    async def stash_event(self, interaction: discord.Interaction, event_id: str):
        event = await self.db.get_event(interaction.guild.id, event_id)
        if event.stashed:
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{NO}**Event is already stashed.**", ephemeral=True)
        else:
            await self.db.set_event_stashed(interaction.guild.id, event_id, True)
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{YES}**Event `{event_id}` stashed.**", ephemeral=True)
            await self.update_schedule_messages(interaction.guild.id)

    # =================
    # /schedule unstash
    # =================
    @app_commands.command(name="unstash", description=desc.cmd_unstash)
    @app_commands.describe(event_id=desc.event_id)
    @app_commands.rename(event_id="id")
    @app_commands.default_permissions(send_messages=True)
    @guild_registered()
    @guild_enabled()
    @author_is_editor()
    @validate_arguments
    async def unstash_event(self, interaction: discord.Interaction, event_id: str):
        event = await self.db.get_event(interaction.guild.id, event_id)
        if not event.stashed:
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{NO}**Event is not stashed.**", ephemeral=True)
        else:
            await self.db.set_event_stashed(interaction.guild.id, event_id, False)
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{YES}**Event `{event_id}` unstashed.**", ephemeral=True)
            await self.update_schedule_messages(interaction.guild.id)

    # ===============
    # /schedule title
    # ===============
    @app_commands.command(name="title", description=desc.cmd_title)
    @app_commands.describe(event_id=desc.event_id, title=desc.title)
    @app_commands.rename(event_id="id")
    @app_commands.default_permissions(send_messages=True)
    @guild_registered()
    @guild_enabled()
    @author_is_editor()
    @validate_arguments
    async def set_event_title(self, interaction: discord.Interaction, event_id: str, title: str):
        await self.db.set_event_title(interaction.guild.id, event_id, title)
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(f"{YES}**Title of event `{event_id}` edited.**", ephemeral=True)
        await self.update_schedule_messages(interaction.guild.id)

    # =============
    # /schedule url
    # =============
    @app_commands.command(name="url", description=desc.cmd_url)
    @app_commands.describe(event_id=desc.event_id, url=desc.url)
    @app_commands.rename(event_id="id")
    @app_commands.default_permissions(send_messages=True)
    @guild_registered()
    @guild_enabled()
    @author_is_editor()
    @validate_arguments
    async def set_event_url(self, interaction: discord.Interaction, event_id: str, url: str = ""):
        await self.db.set_event_url(interaction.guild.id, event_id, url)
        if url:
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{YES}**URL of event `{event_id}` edited.**", ephemeral=True)
        else:
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{YES}**URL of event `{event_id}` removed.**", ephemeral=True)
        await self.update_schedule_messages(interaction.guild.id)

    # ==============
    # /schedule note
    # ==============
    @app_commands.command(name="note", description=desc.cmd_note)
    @app_commands.describe(event_id=desc.event_id, note=desc.note)
    @app_commands.rename(event_id="id")
    @app_commands.default_permissions(send_messages=True)
    @guild_registered()
    @guild_enabled()
    @author_is_editor()
    @validate_arguments
    async def set_event_note(self, interaction: discord.Interaction, event_id: str, note: str = ""):
        await self.db.set_event_note(interaction.guild.id, event_id, note)
        if note:
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{YES}**Note of event `{event_id}` edited.**", ephemeral=True)
        else:
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{YES}**Note of event `{event_id}` removed.**", ephemeral=True)
        await self.update_schedule_messages(interaction.guild.id)

    # ==============
    # /schedule date
    # ==============
    @app_commands.command(name="date", description=desc.cmd_date)
    @app_commands.describe(event_id=desc.event_id, date=desc.date)
    @app_commands.rename(event_id="id")
    @app_commands.default_permissions(send_messages=True)
    @guild_registered()
    @guild_enabled()
    @author_is_editor()
    @validate_arguments
    async def set_event_date(self, interaction: discord.Interaction, event_id: str, date: str = ""):
        if date:
            datetime, granularity = parse_date(date)
            event_datetime = (await self.db.get_event(interaction.guild.id, event_id)).datetime
            if event_datetime.hour != 23 and event_datetime.month != 59 and event_datetime.second != 59:
                datetime = parse_time(event_datetime.strftime("%H:%M:%S"), datetime)
            await self.db.set_event_datetime(interaction.guild.id, event_id, datetime)
            await self.db.set_event_datetime_granularity(interaction.guild.id, event_id, granularity)
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{YES}**Date of event `{event_id}` edited.**", ephemeral=True)
        else:
            await self.db.set_event_datetime(interaction.guild.id, event_id, None)
            await self.db.set_event_datetime_granularity(interaction.guild.id, event_id, DatetimeGranularity())
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{YES}**Date of event `{event_id}` removed.**", ephemeral=True)
        await self.update_schedule_messages(interaction.guild.id)

    # ==============
    # /schedule time
    # ==============
    @app_commands.command(name="time", description=desc.cmd_time)
    @app_commands.describe(event_id=desc.event_id, time=desc.time)
    @app_commands.rename(event_id="id")
    @app_commands.default_permissions(send_messages=True)
    @guild_registered()
    @guild_enabled()
    @author_is_editor()
    @validate_arguments
    async def set_event_time(self, interaction: discord.Interaction, event_id: str, time: str = ""):
        current_datetime = (await self.db.get_event(interaction.guild.id, event_id)).datetime
        if time:
            datetime = parse_time(time, current_datetime)
            await self.db.set_event_datetime(interaction.guild.id, event_id, datetime)
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{YES}**Time of event `{event_id}` edited.**", ephemeral=True)
        else:
            datetime, _ = parse_date(current_datetime.strftime("%Y/%m/%d"))
            await self.db.set_event_datetime(interaction.guild.id, event_id, datetime)
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{YES}**Time of event `{event_id}` removed.**", ephemeral=True)
        await self.update_schedule_messages(interaction.guild.id)

    # ==============
    # /schedule type
    # ==============
    @app_commands.command(name="type", description=desc.cmd_type)
    @app_commands.describe(event_id=desc.event_id, event_type=desc.event_type)
    @app_commands.autocomplete(event_type=type_autocomplete)
    @app_commands.rename(event_id="id", event_type="type")
    @app_commands.default_permissions(send_messages=True)
    @guild_registered()
    @guild_enabled()
    @author_is_editor()
    @validate_arguments
    async def set_event_type(self, interaction: discord.Interaction, event_id: str, event_type: str = ""):
        if event_type:
            await self.db.set_event_type(interaction.guild.id, event_id, parse_type(event_type))
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(f"{YES}**Type of event `{event_id}` edited.**", ephemeral=True)
        else:
            await self.db.set_event_type(interaction.guild.id, event_id, 4)
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(
                f"{YES}**Type of event `{event_id}` set to `other`.**", ephemeral=True
            )
        await self.update_schedule_messages(interaction.guild.id)

    # =================
    # /schedule refresh
    # =================
    @app_commands.command(name="refresh", description=desc.cmd_refresh)
    @app_commands.default_permissions(send_messages=True)
    @guild_registered()
    @guild_enabled()
    @author_is_editor()
    async def refresh_schedule(self, interaction: discord.Interaction):
        # noinspection PyUnresolvedReferences
        await interaction.response.defer(ephemeral=True)
        await self.update_schedule_messages(interaction.guild.id)
        await interaction.followup.send(content=f"{YES}**Schedule refreshed.**")

    # =================
    # /schedule history
    # =================
    @app_commands.command(name="history", description=desc.cmd_history)
    @app_commands.default_permissions(send_messages=True)
    @guild_registered()
    async def history(self, interaction: discord.Interaction):
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(f"{NO}**Command not implemented.**", ephemeral=True)


async def setup(client: Onigiri):
    schedule = Schedule(client)
    await client.add_cog(schedule)
    for cmd in client.tree.walk_commands():
        if isinstance(cmd, discord.app_commands.Group):
            if cmd.name == "schedule":
                cmd.add_command(schedule.Config(parent_cog=schedule))
