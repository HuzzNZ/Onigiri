import os
from functools import wraps
from datetime import datetime, timedelta
from typing import List, Union, Optional, Literal

import asyncio
from dotenv import load_dotenv

import discord
from discord import app_commands
from discord.ui import View, Button, button
from discord.ext import commands, tasks
from discord.ext.commands import Context, Greedy

from apis.database_api import OnigiriDB
from apis.youtube_api import YouTubeURL

from tools import log_time, render_schedule, validate_yt
from tools.constants import *

load_dotenv()


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
        guild = self.db.get_guild(guild_id)
        print(f"{log_time()}Updating schedule for guild {guild.name} ({guild.id}).")

        if not guild:
            print(f"{log_time()}    ↳ {guild_id}: This instance is not in the guild.")
            print(f"{log_time()}")
            return

        events = self.db.get_guild_events(guild_id)
        channel = self.get_channel(guild.get("schedule_channel_id"))
        if not channel:
            raise discord.NotFound

        message = await channel.fetch_message(guild.get("schedule_message_id"))
        content = render_schedule(guild, events)
        print(f"{log_time()}    ↳ {guild_id}: Message length currently {len(content)}")

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
            except ValueError:
                print(f"{log_time()}    "
                      f"↳ {guild.get('guild_id')}: Schedule message or channel not found.")
                print(f"{log_time()}")

    @loop_refresh.before_loop
    async def before_loop(self):
        await self.wait_until_ready()


if __name__ == "__main__":
    bot = Onigiri()
    tree = bot.tree


    class NoGuildFound(discord.app_commands.CheckFailure):
        def __init__(self, message=""):
            super(NoGuildFound, self).__init__(message)

    # Decorators


    def check_guild_perms(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                interaction: discord.Interaction = args[0]
                guild = interaction.client.db.check_guild_exists(interaction.guild.id)
            except AttributeError:
                interaction: discord.Interaction = args[1]
                guild = interaction.client.db.check_guild_exists(interaction.guild.id)
            if guild:
                if guild.get('enabled'):
                    try:
                        return await func(*args, **kwargs)
                    except discord.Forbidden:
                        error = "**Command failed.** Check that the bot has the permissions to **view**, " \
                                "and **send messages** in the schedule channel."
                    except discord.NotFound:
                        error = "**Command failed.** The schedule channel / message no longer exists! Please run **/setup**."
                else:
                    error = "I'm currently **disabled** on the server! Please run **/enable** to enable me again."
            else:
                raise NoGuildFound
            try:
                await interaction.response.send_message(NO + error, ephemeral=True)
            except discord.InteractionResponded:
                try:
                    await interaction.edit_original_message(content=NO + error)
                except discord.InteractionResponded:
                    await interaction.followup.send(content=NO + error, ephemeral=True)

        return wrapper


    def check_event_id(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            interaction: discord.Interaction = args[0]
            event_id = kwargs.get("event_id")[:4]
            kwargs["event_id"] = event_id
            event = interaction.client.db.check_event_exists(interaction.guild.id, event_id)
            if event:
                return await func(*args, **kwargs)
            else:
                error = f"**No event with ID `{event_id}` found!**"
                await interaction.response.send_message(NO + error, ephemeral=True)

        return wrapper


    def check_date_time(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            interaction: discord.Interaction = args[0]
            try:
                return await func(*args, **kwargs)
            except ValueError:
                error = f"**Bad date/time input.** Please check your input again for errors."
                await interaction.response.send_message(NO + error, ephemeral=True)

        return wrapper


    def check_title(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            interaction: discord.Interaction = args[0]
            title: str = kwargs.get("title", "")
            if title is not None:
                if len(title) > 30:
                    return await interaction.response.send_message(
                        f"{NO}**Title too long!** Max 30 characters. (Currently {len(title)})", ephemeral=True)
                elif not title:
                    return await interaction.response.send_message(
                        f"{NO}**Title cannot be empty!**", ephemeral=True)
            return await func(*args, **kwargs)

        return wrapper


    def check_url(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            interaction: discord.Interaction = args[0]
            event_id: str = kwargs.get("event_id", "")
            url: str = kwargs.get("url")
            if url:
                if not (url.startswith("http://") or url.startswith("https://")):
                    return await interaction.response.send_message(
                        f"{NO}**Invalid URL!** URLs should begin with `http://` or `https://`.", ephemeral=True)
                yt_id = validate_yt(url)
                if yt_id:
                    video = YouTubeURL(yt_id)
                    if video.valid:
                        await interaction.response.defer(ephemeral=True)
                        confirm = PopulateFromURLView()
                        timestamp = f"<t:{int(video.get_datetime_jst().timestamp())}:f>"
                        if event_id:
                            title = interaction.client.db.get_event(interaction.guild.id, event_id).get("title")
                        else:
                            title = kwargs.get("title", '') or video.get_event_title()
                        await interaction.followup.send(
                            content=
                            f"{YT}  **YouTube link found.**\n\n"
                            f"> **Title**: {title}\n"
                            f"> **URL**: <{video.url}>\n"
                            f"> **Timestamp**: {timestamp}\n"
                            f"> **Type**: `{EVENT_TYPES[video.get_event_type()]}`\n\n"
                            f"**Do you want to use these for the event?**", view=confirm, ephemeral=True)
                        timeout = await confirm.wait()
                        if not timeout:
                            if confirm.value:
                                if not event_id:
                                    event_id = interaction.client.db.add_event(
                                        interaction.guild.id,
                                        title,
                                        video.get_event_type(),
                                        video.url,
                                        video.get_datetime_jst(),
                                        True
                                    )
                                    message = f"{YES}**Event `{event_id}` added!**"
                                else:
                                    interaction.client.db.edit_event(
                                        interaction.guild.id,
                                        event_id,
                                        title,
                                        video.get_event_type(),
                                        video.url,
                                        video.get_datetime_jst(),
                                        True
                                    )
                                    message = f"{YES}**Event `{event_id}` updated.**"
                                await interaction.edit_original_message(
                                    content=message, view=None)
                                return await interaction.client.update_schedule(interaction.guild.id)
                            else:
                                await interaction.edit_original_message(
                                    content=f"{CANCELLED}  **Ignoring YouTube link...**", view=None)
                                await asyncio.sleep(1)
                        else:
                            await interaction.edit_original_message(
                                content=f"{CANCELLED}  **Confirmation timed out, ignoring YouTube link...**", view=None)
                            await asyncio.sleep(1)
            return await func(*args, **kwargs)
        return wrapper


    async def manage_messages(interaction: discord.Interaction) -> bool:
        guild = interaction.client.db.check_guild_exists(interaction.guild.id)
        if not guild:
            raise NoGuildFound
        try:
            guild_channel = interaction.client.get_channel(guild.get("schedule_channel_id"))
            perms = guild_channel.permissions_for(interaction.user).manage_messages
            if not perms:
                if guild.get("editor_role_id"):
                    editor_role = interaction.guild.get_role(guild.get("editor_role_id"))
                    perms = editor_role in interaction.user.roles
            return perms
        except discord.NotFound:
            return False


    async def manage_channels(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.manage_channels


    class ConfirmView(View):
        def __init__(self):
            super().__init__(timeout=60)
            self.value = None

        @button(label='Confirm', style=discord.ButtonStyle.danger)
        async def confirm(self, interaction: discord.Interaction, b: Button):
            self.value = True
            self.stop()

        @button(label='Cancel', style=discord.ButtonStyle.secondary)
        async def cancel(self, interaction: discord.Interaction, b: Button):
            self.value = False
            self.stop()


    class PopulateFromURLView(View):
        def __init__(self):
            super().__init__(timeout=300)
            self.value = None

        @button(label='Use all', style=discord.ButtonStyle.blurple)
        async def replace_all(self, interaction: discord.Interaction, b: Button):
            self.value = True
            self.stop()

        @button(label="Don't use", style=discord.ButtonStyle.secondary)
        async def cancel(self, interaction: discord.Interaction, b: Button):
            self.value = False
            self.stop()


    # Maintenance / Utility Commands


    @tree.command(description="Must be run at least once! "
                              "Sets up the bot, or edits schedule channel for the server.")
    @app_commands.describe(channel="The channel to keep the schedule message in.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.check(manage_channels)
    async def setup(interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)

        guild_id = interaction.guild.id
        schedule_channel_id = channel.id

        current_channel = interaction.client.db.get_guild(guild_id).get("schedule_channel_id")
        if not current_channel or current_channel != schedule_channel_id:
            try:
                message = await interaction.client.new_schedule(guild_id, schedule_channel_id)
            except discord.Forbidden:
                await interaction.followup.send(
                    f"{NO}**Setup failed.** Check that the bot has the permissions to **view**, "
                    "and **send messages** in the correct channel.")
                return

            interaction.client.db.add_or_edit_guild(guild_id, schedule_channel_id, message.id)
            await interaction.client.update_schedule(guild_id)
            await interaction.followup.send(
                f"{YES}**The schedule message channel has been set to <#{schedule_channel_id}>**, "
                f"and a new message was created.\n> <{message.jump_url}>")
        else:
            await interaction.followup.send(
                f"{NO}**The schedule message channel is already <#{schedule_channel_id}>**.")


    @tree.command(description="Disables the bot on this server. (Does not remove event data!)")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.check(manage_channels)
    async def disable(interaction: discord.Interaction):
        guild = interaction.client.db.check_guild_exists(interaction.guild.id)
        if guild:
            result = interaction.client.db.disable_guild(interaction.guild.id)
            await interaction.response.send_message(
                f"{YES}**Bot disabled.** You can use **/enable** to enable me again!" if result else
                f"{NO}**Bot is already disabled.**", ephemeral=True
            )
        else:
            error = "**This server has not yet been set up!** Please run **/setup** first."
            await interaction.response.send_message(NO + error, ephemeral=True)
        await interaction.client.update_schedule(interaction.guild.id)


    @tree.command(description="Enables the bot on this server.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.check(manage_channels)
    async def enable(interaction: discord.Interaction):
        guild = interaction.client.db.check_guild_exists(interaction.guild.id)
        if guild:
            result = interaction.client.db.enable_guild(interaction.guild.id)
            await interaction.response.send_message(
                f"{YES}**Bot enabled!** You can use **/disable** to disable me again." if result else
                f"{NO}**Bot is already enabled.**", ephemeral=True
            )
        else:
            error = "**This server has not yet been set up!** Please run **/setup** first."
            await interaction.response.send_message(NO + error, ephemeral=True)
        await interaction.client.update_schedule(interaction.guild.id)


    @tree.command(name="set-editor", description="Sets a role that can access commands to edit the schedule.")
    @app_commands.describe(editor="The role to set as an editor.")
    @app_commands.rename(editor="role")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @check_guild_perms
    @app_commands.check(manage_channels)
    async def set_editor(interaction: discord.Interaction, editor: discord.Role = None):
        editor_id = editor.id if editor else None
        interaction.client.db.edit_guild_editor(interaction.guild.id, editor_id)
        await interaction.response.send_message(
            f"{YES}The schedule editor role has been set to **{editor.name}**." if editor else
            f"{YES}The schedule editor role has been **reset**.", ephemeral=True)


    @tree.command(name="set-description", description="Sets a description that appears on top of the schedule.")
    @app_commands.describe(description="The description to set. "
                                       "Formatting will not work, but emojis will. (Max 200 characters)")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @check_guild_perms
    @app_commands.check(manage_channels)
    async def set_description(interaction: discord.Interaction, description: str = ""):
        if len(description) > 200:
            await interaction.response.send_message(f"{NO}**Description too long.** Max 200 characters. "
                                                    f"(Currently {len(description)})\n"
                                                    f"> **Tip:** *You can click on the **`... used /set-description`** "
                                                    f"on top of this message to retrieve your last command!*",
                                                    ephemeral=True)
            return
        interaction.client.db.edit_guild_description(interaction.guild.id, description)
        await interaction.response.send_message(
            f"{YES}**The description has been set.**" if description else
            f"{YES}**The description has been reset.**", ephemeral=True)
        await interaction.client.update_schedule(interaction.guild.id)


    @tree.command(name="set-talent", description="Sets the name of the talent the schedule is for.")
    @app_commands.describe(name="The name of talent that the schedule is for. (Max 40 characters)")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @check_guild_perms
    @app_commands.check(manage_channels)
    async def set_talent(interaction: discord.Interaction, name: str = ""):
        if len(name) > 40:
            await interaction.response.send_message(f"{NO}**Talent name too long.** Max 40 characters. "
                                                    f"(Currently {len(name)})\n"
                                                    f"> **Tip:** *You can click on the **`... used /set-talent`** "
                                                    f"on top of this message to retrieve your last command!*",
                                                    ephemeral=True)
            return
        interaction.client.db.edit_guild_talent(interaction.guild.id, name)
        await interaction.response.send_message(
            f"{YES}The talent has been set to **{name}**." if name else
            f"{YES}The talent has been **reset**.", ephemeral=True)
        await interaction.client.update_schedule(interaction.guild.id)


    @tree.command(name="server-info", description="This server's configuration at a glance.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @check_guild_perms
    @app_commands.check(manage_channels)
    async def server_info(interaction: discord.Interaction):
        guild = interaction.client.db.get_guild(interaction.guild.id)
        editor_role_mention = f"<@&{guild.get('editor_role_id')}>" if guild.get('editor_role_id') else "`None`"
        msg = f"__**{interaction.guild.name}'s {interaction.client.user.mention} Configuration**__\n\n" \
              f"> **Enabled**: {YES if guild.get('enabled') else NO}\n> \n" \
              f"> **Editor Role**: {editor_role_mention}\n> \n" \
              f"> **Talent Name**: {guild.get('talent', '`None`')}\n> \n" \
              f"> **Description**: {guild.get('description', '`None`')}\n> \n" \
              f"> **Schedule Channel**: <#{guild.get('schedule_channel_id')}>\n" \
              f"> **Schedule Message ID**: `{guild.get('schedule_message_id')}`"
        await interaction.response.send_message(content=msg, ephemeral=True)


    @app_commands.default_permissions(manage_channels=True)
    class Reset(app_commands.Group):
        def __init__(self):
            super().__init__(description="Resets various things in the server.")

        @app_commands.command(description="Resets all future events in this server.")
        @app_commands.guild_only()
        @app_commands.default_permissions(manage_channels=True)
        @check_guild_perms
        @app_commands.check(manage_channels)
        async def future(self, interaction: discord.Interaction):
            await interaction.response.send_message(f"{NO}**Not implemented yet!**", ephemeral=True)

        @app_commands.command(description="Resets all past events in this server.")
        @app_commands.guild_only()
        @app_commands.default_permissions(manage_channels=True)
        @check_guild_perms
        @app_commands.check(manage_channels)
        async def past(self, interaction: discord.Interaction):
            await interaction.response.send_message(f"{NO}**Not implemented yet!**", ephemeral=True)

        @app_commands.command(description="Resets all events in this server.")
        @app_commands.guild_only()
        @app_commands.default_permissions(manage_channels=True)
        @check_guild_perms
        @app_commands.check(manage_channels)
        async def events(self, interaction: discord.Interaction):
            await interaction.response.send_message(f"{NO}**Not implemented yet!**", ephemeral=True)

        @app_commands.command(description="Resets all configuration in this server.")
        @app_commands.guild_only()
        @app_commands.default_permissions(manage_channels=True)
        @check_guild_perms
        @app_commands.check(manage_channels)
        async def config(self, interaction: discord.Interaction):
            await interaction.response.send_message(f"{NO}**Not implemented yet!**", ephemeral=True)

        @app_commands.command(description="Resets all events, and all configuration in this server.")
        @app_commands.guild_only()
        @app_commands.default_permissions(manage_channels=True)
        @check_guild_perms
        @app_commands.check(manage_channels)
        async def all(self, interaction: discord.Interaction):
            await interaction.response.send_message(f"{NO}**Not implemented yet!**", ephemeral=True)


    @tree.command(description="Manually refreshes the schedule message.")
    @app_commands.guild_only()
    @check_guild_perms
    @app_commands.check(manage_messages)
    async def refresh(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.client.update_schedule(interaction.guild.id)
        await interaction.followup.send(content=f"{YES}**Schedule refreshed.**", ephemeral=True)


    @tree.command(description="Pong!")
    async def ping(interaction: discord.Interaction):
        await interaction.response.send_message(f"{interaction.user.mention} Pong!", ephemeral=True)

    @tree.command(name="help", description="Links to the documentation page for the bot.")
    async def help_command(interaction: discord.Interaction):
        await interaction.response.send_message(f"**Check out the documentations here:**\n"
                                                f"> <https://huzz.notion.site/Onigiri-Bot-"
                                                f"Documentation-85760679057645aca767b94c867f3fd7>", ephemeral=True)


    # Autocomplete for event types


    async def type_ac(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        types = ['stream', 'video', 'event', 'release', 'other']
        choices = []
        for i in range(len(types)):
            if current.lower() in types[i]:
                choices.append(app_commands.Choice(name=types[i], value=types[i]))
        return choices


    # Event Creation Commands


    def parse_date(date_str: str) -> Union[datetime, None]:
        if not date_str:
            return None
        date_str = date_str.lower()
        now = datetime.now(JST)
        year, month, day = now.year, 0, 0
        using_current_year = True
        if "today" in date_str:
            month = now.month
            day = now.day
        elif "tomorrow" in date_str:
            tomorrow = now + timedelta(days=1)
            year, month, day = tomorrow.year, tomorrow.month, tomorrow.day
        if "/" in date_str:
            dates = date_str.split("/")
            if len(dates) == 2:
                if 0 < int(dates[0]) <= 12:
                    month = int(dates[0])
                if 0 < int(dates[0]) <= 31:
                    day = int(dates[1])
            elif len(dates) > 2:
                if int(dates[0]) < 100:
                    year = 2000 + int(dates[0])
                    using_current_year = False
                elif 3000 > int(dates[0]) > 2000:
                    year = int(dates[0])
                    using_current_year = False
                else:
                    raise ValueError
                month = int(dates[1])
                day = int(dates[2])
        else:
            dates = date_str.replace(",", " ").split(" ")
            for date in dates:
                if not month:
                    for i in range(len(MONTHS)):
                        if MONTHS[i] in date:
                            month = i + 1
                            break
            numbers = [int(x) for x in dates if x.isdigit()]
            for n in numbers:
                if 0 < n <= 31 and not day:
                    day = n
                elif 3000 > n > 2000:
                    year = n
                    using_current_year = False

        if not month or not day:
            raise ValueError
        else:
            if using_current_year and month < datetime.now(JST).month:
                year += 1
            return datetime(year, month, day, 14, 59, 59, 0).replace(
                tzinfo=pytz.utc).astimezone(JST)


    def parse_time(time_str: str, dt: datetime = None) -> Union[datetime, None]:
        if not dt or not time_str:
            return None
        time_str = time_str.lower()
        h, m = None, None

        day_offset = 0
        if "now" in time_str:
            now = datetime.now(JST)
            h = now.hour
            m = now.minute
        elif len(time_str) == 4 and time_str.isdigit():
            if 29 >= int(time_str[:2]) >= 0:
                h = int(time_str[:2])
                if 29 >= h >= 24:
                    day_offset = 1
                    h %= 24
            if 60 > int(time_str[2:]) >= 0:
                m = int(time_str[2:])
        elif ":" in time_str:
            times = time_str.split(":")
            if 2 <= len(times) <= 3:
                times.append("")
                if 29 >= int(times[0]) >= 0:
                    if 29 >= int(times[0]) >= 24:
                        day_offset = 1
                        h = int(times[0]) % 24
                    else:
                        h = int(times[0])
                else:
                    raise ValueError
                if "am" in times[1] or "am" in times[2]:
                    if h <= 0 or h > 12:
                        raise ValueError
                    times[1] = times[1].replace("am", "").strip()
                    if 0 <= int(times[1]) < 60:
                        m = int(times[1])
                    if h == 12:
                        h = 0
                elif "pm" in times[1] or "pm" in times[2]:
                    if h <= 0 or h > 12:
                        raise ValueError
                    times[1] = times[1].replace("pm", "").strip()
                    if 0 <= int(times[1]) < 60:
                        m = int(times[1])
                    if h < 12:
                        h += 12
                else:
                    if 0 <= int(times[1]) < 60:
                        m = int(times[1])
        else:
            h = int(time_str.replace("am", "").replace("pm", "").strip())
            if not 29 >= h >= 0:
                raise ValueError
            if 29 >= h >= 24:
                day_offset = 1
                h %= 24
            if "am" in time_str:
                if h <= 0 or h > 12:
                    raise ValueError
                if h == 12:
                    h = 0
            elif "pm" in time_str:
                if h <= 0 or h > 12:
                    raise ValueError
                if h < 12:
                    h += 12
            m = 0
        if h is None or m is None:
            raise ValueError
        else:
            return dt.replace(second=0, minute=m, hour=h) + timedelta(days=day_offset)


    def parse_type(event_type: str) -> int:
        match event_type:
            case "stream":
                return 0
            case "video":
                return 1
            case "event":
                return 2
            case "release":
                return 3
            case "other":
                return 4
        return 4


    @tree.command(description="Adds an event to the schedule.")
    @app_commands.describe(
        title="The title of the event. Max 30 characters. Try to keep it short and concise!",
        event_type="The type of the event. Defaults to stream.",
        url="The URL/Link of an event. YouTube stream/premiere URLs can be picked up.",
        date="The date of the event in JST. (e.g. Jul 12, 22/7/12, 7/12, 12 Jul 2022, today, tomorrow, etc.)",
        time="The time of the event in JST. (e.g. 8:00 pm, 20:00, 20, 3am, 27:00, now, etc.)")
    @app_commands.guild_only()
    @app_commands.autocomplete(event_type=type_ac)
    @app_commands.rename(event_type="type")
    @check_guild_perms
    @check_date_time
    @check_title
    @check_url
    @app_commands.check(manage_messages)
    async def add(interaction: discord.Interaction,
                  title: str, url: str = "", date: str = "", time: str = "", event_type: str = 'stream'):
        dt = None
        if date:
            dt = parse_date(date)
            if time:
                dt = parse_time(time, dt)
        t = parse_type(event_type)
        event_id = interaction.client.db.add_event(interaction.guild_id, title, t, url, dt)
        try:
            await interaction.response.send_message(f"{YES}**Event `{event_id}` added!**", ephemeral=True)
        except discord.InteractionResponded:
            await interaction.edit_original_message(content = f"{YES}**Event `{event_id}` added!**")
        await interaction.client.update_schedule(interaction.guild.id)


    @tree.command(name="add-yt", description="Adds an event to the schedule using a YouTube URL.")
    @app_commands.describe(
        url="The YouTube URL linking to a video, premiere, or stream.",
        title="The title of the event. Max 30 characters. Defaults to the title of the YouTube video/stream.")
    @app_commands.guild_only()
    @check_guild_perms
    @check_title
    @check_url
    @app_commands.check(manage_messages)
    async def add_yt(interaction: discord.Interaction, url: str, title: str = None):
        try:
            await interaction.response.send_message(f"{NO}**No valid YouTube link found.**", ephemeral=True)
        except discord.InteractionResponded:
            await interaction.edit_original_message(content=f"{NO}**Cancelled.**")
        await interaction.client.update_schedule(interaction.guild.id)


    @tree.command(description="Deletes an event from the schedule.")
    @app_commands.describe(event_id=EVENT_ID_DESC)
    @app_commands.rename(event_id="id")
    @app_commands.guild_only()
    @check_guild_perms
    @check_event_id
    @app_commands.check(manage_messages)
    async def delete(interaction: discord.Interaction, event_id: str):
        confirm = ConfirmView()
        await interaction.response.send_message(
            f"{WARNING}  **Are you sure you want to delete event `{event_id}`?**\n"
            f"> If the event was cancelled, consider using **/stash `{event_id}`**.", view=confirm, ephemeral=True)
        timeout = await confirm.wait()
        if not timeout:
            if confirm.value:
                interaction.client.db.delete_event(interaction.guild.id, event_id)
                await interaction.edit_original_message(content=f"{YES}**Event `{event_id}` deleted.**", view=None)
                await interaction.client.update_schedule(interaction.guild.id)
            else:
                await interaction.edit_original_message(content=f"{CANCELLED}  **Cancelled.**", view=None)
        else:
            await interaction.edit_original_message(content=f"{CANCELLED}  **Confirmation timed out.**", view=None)


    @tree.command(description="Edits an event. Only edits the fields supplied.")
    @app_commands.describe(event_id=EVENT_ID_DESC)
    @app_commands.describe(
        title="The title of the event. Max 30 characters. Try to keep it short and concise!",
        event_type="The type of the event. Defaults to stream.",
        url="The URL/Link of an event. YouTube stream/premiere URLs can be picked up.",
        date="The date of the event in JST. (e.g. Jul 12, 22/7/12, 7/12, 12 Jul 2022, today, tomorrow, etc.)",
        time="The time of the event in JST. (e.g. 8:00 pm, 20:00, 20, 3am, 27:00, etc.)",
        note="The note to the event. Max 30 characters.")
    @app_commands.rename(event_id="id")
    @app_commands.rename(event_type="type")
    @app_commands.guild_only()
    @app_commands.autocomplete(event_type=type_ac)
    @check_guild_perms
    @check_event_id
    @check_title
    @check_url
    @app_commands.check(manage_messages)
    async def edit(interaction: discord.Interaction, event_id: str,
                   title: str = None, url: str = "", date: str = "", time: str = "",
                   event_type: str = 'stream', note: str = ''):
        if date:
            dt = parse_date(date)
            if time:
                dt = parse_time(time, dt)
            interaction.client.db.edit_event_datetime(interaction.guild.id, event_id, dt)
        elif time:
            date_dt = interaction.client.db.get_event(interaction.guild.id, event_id).get("datetime")
            if not date_dt:
                try:
                    await interaction.response.send_message(
                        f"{NO}**No date set on event!** Please add a date, or use **/date `{event_id}`** first.",
                        ephemeral=True)
                except discord.InteractionResponded:
                    await interaction.edit_original_message(
                        content=f"{NO}**No date set on event!** Please add a date, use **/date `{event_id}`** first.")
                return
            else:
                dt = parse_time(time, date_dt)
                interaction.client.db.edit_event_datetime(interaction.guild.id, event_id, dt)
        if title:
            interaction.client.db.edit_event_title(interaction.guild.id, event_id, title)
        if url:
            interaction.client.db.edit_event_url(interaction.guild.id, event_id, url)
        if event_type:
            interaction.client.db.edit_event_type(interaction.guild.id, event_id, parse_type(event_type))
        if note:
            if len(note) > 30:
                try:
                    await interaction.response.send_message(f"{NO}**Note too long.** Max 30 characters. "
                                                            f"(Currently {len(note)})\n"
                                                            f"> **Tip:** *You can click on the **`... used /edit`** "
                                                            f"on top of this message to retrieve your last command!*",
                                                            ephemeral=True)
                except discord.InteractionResponded:
                    await interaction.edit_original_message(
                        content=f"{NO}**Note too long.** Max 30 characters. "
                                f"(Currently {len(note)})\n"
                                f"> **Tip:** *You can click on the **`... used /edit`** "
                                f"on top of this message to retrieve your last command!*")
                return
            interaction.client.db.edit_event_note(interaction.guild.id, event_id, note)
        try:
            await interaction.response.send_message(f"{YES}**Event `{event_id}` updated.**", ephemeral=True)
        except discord.InteractionResponded:
            await interaction.edit_original_message(content=f"{YES}**Event `{event_id}` updated.**")
        await interaction.client.update_schedule(interaction.guild.id)


    @tree.command(name="title", description="Edits the title of an event.")
    @app_commands.describe(event_id=EVENT_ID_DESC)
    @app_commands.describe(title="The title of the event. Max 30 characters.")
    @app_commands.guild_only()
    @app_commands.rename(event_id="id")
    @check_guild_perms
    @check_event_id
    @check_title
    @app_commands.check(manage_messages)
    async def edit_title(interaction: discord.Interaction, event_id: str, title: str):
        interaction.client.db.edit_event_title(interaction.guild.id, event_id, title)
        await interaction.response.send_message(f"{YES}**Title of event `{event_id}` updated.**", ephemeral=True)
        await interaction.client.update_schedule(interaction.guild.id)


    @tree.command(name="url", description="Edits the URL of an event. Enter nothing to reset the URL. "
                                          "Recognizes YouTube streams and premieres.")
    @app_commands.describe(event_id=EVENT_ID_DESC)
    @app_commands.describe(url="The URL/Link of an event. YouTube stream/premiere URLs can be picked up. "
                               "Enter nothing to clear the URL.")
    @app_commands.guild_only()
    @app_commands.rename(event_id="id")
    @check_guild_perms
    @check_event_id
    @check_url
    @app_commands.check(manage_messages)
    async def edit_url(interaction: discord.Interaction, event_id: str, url: str = ""):
        reset = False if url else True
        interaction.client.db.edit_event_url(interaction.guild.id, event_id, url)
        if reset:
            interaction.client.db.edit_event_confirmed(interaction.guild.id, event_id, False)
        try:
            await interaction.response.send_message(
                f"{YES}**URL of event `{event_id}` {'updated' if not reset else 'reset'}.**", ephemeral=True)
        except discord.InteractionResponded:
            await interaction.edit_original_message(
                content=f"{YES}**URL of event `{event_id}` {'updated' if not reset else 'reset'}.**")

        await interaction.client.update_schedule(interaction.guild.id)


    @tree.command(name="date", description="Edits the date of an event. "
                                           "Editing the date will reset the time.")
    @app_commands.describe(event_id=EVENT_ID_DESC)
    @app_commands.describe(date="The date of the event in JST. "
                                "(e.g. Jul 12, 22/7/12, 7/12, 12 Jul 2022, today, tomorrow, etc.) "
                                "Enter nothing clear the date.")
    @app_commands.rename(event_id="id")
    @app_commands.guild_only()
    @check_guild_perms
    @check_event_id
    @check_date_time
    @app_commands.check(manage_messages)
    async def edit_date(interaction: discord.Interaction, event_id: str, date: str = ""):
        reset = False
        if date:
            dt = parse_date(date)
        else:
            dt = None
            reset = True
        interaction.client.db.edit_event_datetime(interaction.guild.id, event_id, dt)
        await interaction.response.send_message(
            f"{YES}**Date of event `{event_id}` {'updated' if not reset else 'reset'}.**", ephemeral=True)
        await interaction.client.update_schedule(interaction.guild.id)


    @tree.command(name="time", description="Edits the time of an event. "
                                           "The event must already have a date.")
    @app_commands.describe(event_id=EVENT_ID_DESC)
    @app_commands.describe(time="The time of the event in JST. (e.g. 8:00 pm, 20:00, 20, 3am, 27:00, now, etc.), "
                                "Enter nothing to clear the time.")
    @app_commands.rename(event_id="id")
    @app_commands.guild_only()
    @check_guild_perms
    @check_event_id
    @check_date_time
    @app_commands.check(manage_messages)
    async def edit_time(interaction: discord.Interaction, event_id: str, time: str = ""):
        reset = False
        date_dt = interaction.client.db.get_event(interaction.guild.id, event_id).get("datetime")
        if not date_dt:
            await interaction.response.send_message(
                f"{NO}**No date set on event!** Please use **/date `{event_id}`** first.", ephemeral=True)
            return
        if time:
            dt = parse_time(time, date_dt)
        else:
            dt = parse_date(date_dt.strftime("%b %-d"))
            reset = True
        interaction.client.db.edit_event_datetime(interaction.guild.id, event_id, dt)
        await interaction.response.send_message(
            f"{YES}**Time of event `{event_id}` {'updated' if not reset else 'reset'}.**", ephemeral=True)
        await interaction.client.update_schedule(interaction.guild.id)


    @tree.command(name="type", description="Edits the type of an event.")
    @app_commands.describe(event_id=EVENT_ID_DESC)
    @app_commands.describe(event_type="The type of the event. Enter nothing to set to stream.")
    @app_commands.rename(event_id="id")
    @app_commands.guild_only()
    @app_commands.autocomplete(event_type=type_ac)
    @app_commands.rename(event_type="type")
    @check_guild_perms
    @check_event_id
    @app_commands.check(manage_messages)
    async def edit_type(interaction: discord.Interaction, event_id: str, event_type: str = ""):
        reset = False
        if not event_type:
            reset = True
            event_type = "stream"
        t = parse_type(event_type)
        interaction.client.db.edit_event_type(interaction.guild.id, event_id, t)
        await interaction.response.send_message(
            f"{YES}**Type of event `{event_id}` {'updated' if not reset else 'reset'}.**", ephemeral=True)
        await interaction.client.update_schedule(interaction.guild.id)


    @tree.command(description="Stashes an event. An event will appear crossed out when stashed, "
                              "but it will not be deleted.")
    @app_commands.describe(event_id=EVENT_ID_DESC)
    @app_commands.rename(event_id="id")
    @app_commands.guild_only()
    @check_guild_perms
    @check_event_id
    @app_commands.check(manage_messages)
    async def stash(interaction: discord.Interaction, event_id: str):
        event = interaction.client.db.get_event(interaction.guild.id, event_id)
        is_stashed = event.get("stashed", False)
        if not is_stashed:
            interaction.client.db.edit_event_stashed(interaction.guild.id, event_id, True)
            await interaction.response.send_message(f"{YES}**Event `{event_id}` stashed.**", ephemeral=True)
            await interaction.client.update_schedule(interaction.guild.id)
        else:
            await interaction.response.send_message(f"{NO}**Event `{event_id}` is already stashed!**", ephemeral=True)


    @tree.command(description="Unstashes an event.")
    @app_commands.describe(event_id=EVENT_ID_DESC)
    @app_commands.guild_only()
    @check_guild_perms
    @check_event_id
    @app_commands.check(manage_messages)
    async def unstash(interaction: discord.Interaction, event_id: str):
        event = interaction.client.db.get_event(interaction.guild.id, event_id)
        is_stashed = event.get("stashed", False)
        if is_stashed:
            interaction.client.db.edit_event_stashed(interaction.guild.id, event_id, False)
            await interaction.response.send_message(f"{YES}**Event `{event_id}` unstashed.**", ephemeral=True)
            await interaction.client.update_schedule(interaction.guild.id)
        else:
            await interaction.response.send_message(f"{NO}**Event `{event_id}` is not stashed!**", ephemeral=True)


    @tree.command(name="note", description="Edits the note to an event.")
    @app_commands.describe(event_id=EVENT_ID_DESC)
    @app_commands.describe(note="The note to the event. Max 30 characters. Enter nothing to delete the note.")
    @app_commands.guild_only()
    @app_commands.rename(event_id="id")
    @check_guild_perms
    @check_event_id
    @app_commands.check(manage_messages)
    async def edit_note(interaction: discord.Interaction, event_id: str, note: str = ""):
        if len(note) > 30:
            await interaction.response.send_message(f"{NO}**Note too long.** Max 30 characters. "
                                                    f"(Currently {len(note)})\n"
                                                    f"> **Tip:** *You can click on the **`... used /note`** "
                                                    f"on top of this message to retrieve your last command!*",
                                                    ephemeral=True)
            return
        interaction.client.db.edit_event_note(interaction.guild.id, event_id, note)
        await interaction.response.send_message(f"{YES}**Note to event `{event_id}` updated.**" if note else
                                                f"{YES}**Note to event `{event_id}` deleted.**", ephemeral=True)
        await interaction.client.update_schedule(interaction.guild.id)


    tree.add_command(Reset())


    @tree.error
    async def on_check_failure(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, NoGuildFound):
            await interaction.response.send_message(
                f"{NO}**This server has not yet been set up!** Please run **/setup** first.", ephemeral=True)
        elif isinstance(error, discord.app_commands.CheckFailure):
            await interaction.response.send_message(f"{NO}**Missing permissions.**", ephemeral=True)


    @bot.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(
            ctx: Context, guilds: Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

    bot.run(os.getenv("WAKAME"))
