import asyncio
from typing import List, Union, Optional, Literal
from discord.ext import commands, tasks
from discord import app_commands
import discord
from discord.ext.commands import Context, Greedy
from dotenv import load_dotenv
import os
from db_api import OnigiriDB
from datetime import datetime, timedelta
import pytz
import re
from functools import wraps
from discord.ui import View, Button, button
from yt_api import YouTubeURL

load_dotenv()

# Toggle between global sync or dev server sync
DEV = False
YES = "<:yes:622272511345688596>  "
NO = "<:no:622272511299551254>  "
DD = "<:dd:992623483563561030>"
DR = "<:dr:992624464078585916>"
TR = "<:tr:992625824140361728>"
ED = "<:ed:992627365102485624>"
NONE = "<:none:992656221293264957>"
YT = "<:yt:993353027073364038>"
STASHED = "<:no:622272511299551254>"
WARNING = "⚠️"
CANCELLED = "🚫"
YR = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=" \
     r"|embed\/|v\/)?)([\w\-]+)(\S+)?$"
EMOJIPEDIA = [
    {
        "past": "<:yes:622272511345688596>",
        "confirmed": "▶️",
        "unconfirmed": "💭"
    },
    {
        "past": "🎞️",
        "confirmed": "🎞️",
        "unconfirmed": "🎞️"
    },
    {
        "past": "🎆",
        "confirmed": "🎆",
        "unconfirmed": "🎆"
    },
    {
        "past": "💿",
        "confirmed": "💿",
        "unconfirmed": "💿"
    },
    {
        "past": "✅",
        "confirmed": "▶️",
        "unconfirmed": "💭"
    },
]
JST = pytz.timezone("Asia/Tokyo")
MONTHS = ["jan", 'feb', "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
EVENT_ID_DESC = "The 4-digit numeric ID associated with each event. (e.g. 1902, 6817, etc.)"
EVENT_TYPES = ['stream', 'video', 'event', 'release', 'other']


def validate_yt(link):
    yt_id = ""
    if match := re.search(YR, link, re.IGNORECASE):
        yt_id = match.group(6)
    return yt_id


def log_time():
    return datetime.now().strftime('[%b %d %H:%M:%S]  ')


class Onigiri(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        self.AMOUNT_PAST_DISPLAYED = 3
        self.db = OnigiriDB()
        super().__init__(command_prefix=commands.when_mentioned_or("$"), intents=intents)

    async def setup_hook(self):
        print(f'{log_time()}Logged in as {self.user} (ID: {self.user.id})')
        print(f'{log_time()}Starting refresh loop!')
        self.loop_refresh.start()

    async def refresh(self, guild_id, channel_id=None, talent_name=None):
        print(f"{log_time()}Refreshing guild {guild_id}.")
        guild = self.db.get_guild(guild_id)
        events = self.db.get_guild_events(guild_id)
        channel = self.get_channel(channel_id or guild.get("schedule_channel_id"))
        if not channel:
            raise ValueError

        talent_name: str = talent_name or guild.get("talent")

        time_now = datetime.now(JST)

        def get_headline(talent_name1):
            if talent_name1:
                talent_name_with_possessive = talent_name1 + ("'" if talent_name1.endswith("s") else "'s")
                headline = f'__**{talent_name_with_possessive} unofficial schedule, maintained by this server**__:'
            else:
                headline = "__**A schedule, maintained by this server**__:"
            return headline + "\n(Events with Discord Timestamps are in your **local timezone**," \
                              f" all other times are in **JST**.)\n\n" \
                              f"> *Last refreshed <t:{int(datetime.now().timestamp())}:f>*\n"

        def separate_events(event_list):
            future_list = []
            past_list = []
            unspecified_list = []
            for e in event_list:
                e_datetime = e.get("datetime")
                if e_datetime:
                    if e_datetime > time_now:
                        future_list.append(e)
                    else:
                        past_list.append(e)
                else:
                    unspecified_list.append(e)
            return past_list, future_list, unspecified_list

        def is_generic_date(dt: datetime):
            if dt:
                return dt.hour == 23 and dt.minute == 59 and dt.second == 59

        def will_use_timestamp(e):
            dt: datetime = e.get("datetime")
            return e.get("confirmed") or (e.get('type') == 2 and not is_generic_date(dt))

        def format_event_time(e, r=False):
            dt: datetime = e.get("datetime")
            if dt:
                if will_use_timestamp(e):
                    return f"<t:{int(dt.timestamp())}:{'R' if r else 'f'}>"
                else:
                    now = datetime.now(JST)
                    if dt.year == now.year and dt.month == now.month and dt.day == now.day:
                        base_str = "Today"
                        time_format = ""
                    else:
                        base_str = ""
                        time_format = "%b %-d"
                    if dt.year != now.year and not (now.month == 12 and dt.year - 1 == now.year):
                        time_format += ", %Y"
                    if not is_generic_date(dt):
                        time_format += f"{',' if base_str else ' '} %H:%M"
                    return base_str + dt.strftime(time_format)
            else:
                return "Unknown"

        def is_on_same_day(dt1: datetime, dt2: datetime):
            if not dt1 and not dt2:
                return True
            if not dt1 or not dt2:
                return False
            return dt1.year == dt2.year and dt1.month == dt2.month and dt1.day == dt2.day

        def render_past_events(past_list):
            if not past_list:
                return []
            total_length = len(past_list)
            past_list = past_list[:self.AMOUNT_PAST_DISPLAYED][::-1]
            contents = [f"🗂️  __**Past {min(self.AMOUNT_PAST_DISPLAYED, len(past_list))} Events**__ "
                        f"({total_length} total)"]
            for i in range(len(past_list)):
                e = past_list[i]
                s = "~~" if e.get("stashed") else ""
                is_last = i == len(past_list) - 1
                # Line 1
                contents.append(f"{DD}")
                # Line 2
                contents.append(
                    f"{TR if is_last else DR} {s}`{e.get('event_id')}`{s}  "
                    f"{EMOJIPEDIA[e.get('type')].get('past') if not s else STASHED}  "
                    f"**{s}{format_event_time(e)}{s}**")
                # Line 3
                contents.append(f"{NONE if is_last else DD}{' ' * 13}{s}{e.get('title')}{s}")
                # Line 4
                if e.get("url"):
                    contents.append(f"{NONE if is_last else DD}{' ' * 13}{s}<{e.get('url')}>{s}")
            return contents

        def render_next_up(e):
            url = e.get('url')
            s = "~~" if e.get("stashed") else ""
            emoji = EMOJIPEDIA[e.get('type')].get('confirmed' if e.get('confirmed') else 'unconfirmed') if not s \
                else STASHED
            contents = [
                f"⏰  __**Next Up**__", f"{DD}",
                f"{s}`{e.get('event_id')}`{s}  "
                f"{emoji}  "
                f"**{s}{format_event_time(e)}{s}**"]

            if will_use_timestamp(e):
                contents.append(f"{DD}")

            contents.append(f"{DD}{' ' * 6}**{s}{e.get('title')}{s}**")

            if url:
                contents.append(f"{DD}{' ' * 6}{s}<{url}>{s}")
            if will_use_timestamp(e):
                contents.append(f"{DD}{' ' * 6}{s}{format_event_time(e, True)}{s}")
            return contents

        def render_future(future_list, unspecified_list=None):
            if unspecified_list is None:
                unspecified_list = []
            future_list = future_list[::-1] + unspecified_list
            contents = [f"☁️  __**Upcoming**__"]
            previous_dt = None
            for e in future_list:
                url = e.get('url')
                dt = e.get('datetime')
                s = "~~" if e.get("stashed") else ""
                emoji = (EMOJIPEDIA[e.get('type')].get('confirmed' if e.get('confirmed') else 'unconfirmed')) if not s \
                    else STASHED
                uses_timestamp = will_use_timestamp(e)
                if not is_on_same_day(previous_dt, dt):
                    contents.append(f"{DD}")
                contents.append(
                    f"{DR} {s}`{e.get('event_id')}`{s}  "
                    f"{emoji}  "
                    f"{s}**{format_event_time(e)}**{('  ' + e.get('title')) if not uses_timestamp else ''}{s}")
                if uses_timestamp:
                    contents.append(f"{DD}{' ' * 13}{s}{e.get('title')}{s}")
                if url:
                    contents.append(f"{DD}{' ' * 13}{s}<{url}>{s}")
                previous_dt = dt
            contents.append(f"{ED}")
            return contents

        content_list = [get_headline(talent_name)]

        if events:
            past, future, unspecified = separate_events(events)

            content_list += [""] if guild.get("enabled") or not guild else ["⛔  *Currently disabled.*", ""]
            content_list += render_past_events(past)
            content_list += ["", ""]
            if future:
                content_list += render_next_up(future[-1])
                content_list += [f"{DD}"]
                content_list += render_future(future[:-1], unspecified)
            else:
                content_list += ["Nothing planned in the future. Use **/add**, or **/add-yt** to add some events!"]
        else:
            content_list += ["\nUse **/add**, or **/add-yt** to add some events!"]

        content = "\n".join(content_list)

        if not channel_id:
            try:
                message = await channel.fetch_message(guild.get("schedule_message_id"))
                message = await message.edit(content=content)
            except discord.NotFound:
                message = await channel.send(content=content)
                self.db.add_or_edit_guild(guild_id, channel.id, message.id)
        else:
            message = await channel.send(content=content)
        return message

    @tasks.loop(minutes=5)
    async def loop_refresh(self):
        for guild in self.db.get_all_enabled_guilds():
            await self.refresh(guild.get("guild_id"))

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
                    except ValueError:
                        error = "**Command failed.** The schedule channel no longer exists! Please run **/setup**."
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
                                return await interaction.client.refresh(interaction.guild.id)
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
            perms = guild_channel.permissions_for(interaction.user)
            return perms.manage_messages
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
                              "Sets up the bot, or edits configuration for the server.")
    @app_commands.describe(channel="The channel to keep the schedule message in.")
    @app_commands.describe(name="The name of talent that the schedule is for.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.check(manage_channels)
    async def setup(interaction: discord.Interaction, channel: discord.TextChannel, name: str = None):
        await interaction.response.defer(ephemeral=True)

        guild_id = interaction.guild.id
        schedule_channel_id = channel.id

        current_channel = interaction.client.db.get_guild(guild_id).get("schedule_channel_id")
        if not current_channel or current_channel != schedule_channel_id:
            try:
                message = await interaction.client.refresh(guild_id, schedule_channel_id, name)
            except discord.Forbidden:
                await interaction.followup.send(
                    f"{NO}**Setup failed.** Check that the bot has the permissions to **view**, "
                    "and **send messages** in the correct channel.")
                return
            interaction.client.db.add_or_edit_guild(guild_id, schedule_channel_id, message.id, name)
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
        await interaction.client.refresh(interaction.guild.id)


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
        await interaction.client.refresh(interaction.guild.id)


    @tree.command(description="Sets the name of the talent the schedule is for.")
    @app_commands.describe(name="The name of talent that the schedule is for.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @check_guild_perms
    @app_commands.check(manage_channels)
    async def talent(interaction: discord.Interaction, name: str = ""):
        interaction.client.db.edit_guild_talent(interaction.guild.id, name)
        await interaction.response.send_message(
            f"{YES}The talent has been set to **{name}**." if name else
            f"{YES}The talent has been **reset**.", ephemeral=True)
        await interaction.client.refresh(interaction.guild.id)


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
            await interaction.response.send_message("Reset future events!")

        @app_commands.command(description="Resets all past events in this server.")
        @app_commands.guild_only()
        @app_commands.default_permissions(manage_channels=True)
        @check_guild_perms
        @app_commands.check(manage_channels)
        async def past(self, interaction: discord.Interaction):
            await interaction.response.send_message("Reset past events!")

        @app_commands.command(description="Resets all events in this server.")
        @app_commands.guild_only()
        @app_commands.default_permissions(manage_channels=True)
        @check_guild_perms
        @app_commands.check(manage_channels)
        async def events(self, interaction: discord.Interaction):
            await interaction.response.send_message("Reset events!")

        @app_commands.command(description="Resets all configuration in this server.")
        @app_commands.guild_only()
        @app_commands.default_permissions(manage_channels=True)
        @check_guild_perms
        @app_commands.check(manage_channels)
        async def config(self, interaction: discord.Interaction):
            await interaction.response.send_message("Reset configurations!")

        @app_commands.command(description="Resets all events, and all configuration in this server.")
        @app_commands.guild_only()
        @app_commands.default_permissions(manage_channels=True)
        @check_guild_perms
        @app_commands.check(manage_channels)
        async def all(self, interaction: discord.Interaction):
            await interaction.response.send_message("Reset all!")


    @tree.command(description="Manually refreshes the schedule message.")
    @app_commands.guild_only()
    @check_guild_perms
    @app_commands.check(manage_messages)
    async def refresh(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.client.refresh(interaction.guild.id)
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
            else:
                if int(dates[0]) < 100:
                    year = 2000 + int(dates[0])
                    using_current_year = False
                elif 3000 > int(dates[0]) > 2000:
                    year = int(dates[0])
                    using_current_year = False
                else:
                    raise ValueError
                month = int(dates[0])
                day = int(dates[1])
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
        await interaction.client.refresh(interaction.guild.id)


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
        await interaction.client.refresh(interaction.guild.id)


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
                await interaction.client.refresh(interaction.guild.id)
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
        time="The time of the event in JST. (e.g. 8:00 pm, 20:00, 20, 3am, 27:00, etc.)")
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
                   title: str = None, url: str = "", date: str = "", time: str = "", event_type: str = 'stream'):
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
                        f"{NO}**No date set on event!** Please use **/date `{event_id}`** first.", ephemeral=True)
                except discord.InteractionResponded:
                    await interaction.edit_original_message(
                        content=f"{NO}**No date set on event!** Please use **/date `{event_id}`** first.")
            else:
                dt = parse_time(time, date_dt)
                interaction.client.db.edit_event_datetime(interaction.guild.id, event_id, dt)
        if title:
            interaction.client.db.edit_event_title(interaction.guild.id, event_id, title)
        if url:
            interaction.client.db.edit_event_url(interaction.guild.id, event_id, url)
        if event_type:
            interaction.client.db.edit_event_type(interaction.guild.id, event_id, parse_type(event_type))
        try:
            await interaction.response.send_message(f"{YES}**Event `{event_id}` updated.**", ephemeral=True)
        except discord.InteractionResponded:
            await interaction.edit_original_message(content=f"{YES}**Event `{event_id}` updated.**")
        await interaction.client.refresh(interaction.guild.id)


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
        await interaction.client.refresh(interaction.guild.id)


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

        await interaction.client.refresh(interaction.guild.id)


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
        await interaction.client.refresh(interaction.guild.id)


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
        await interaction.client.refresh(interaction.guild.id)


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
        await interaction.client.refresh(interaction.guild.id)


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
            await interaction.client.refresh(interaction.guild.id)
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
            await interaction.client.refresh(interaction.guild.id)
        else:
            await interaction.response.send_message(f"{NO}**Event `{event_id}` is not stashed!**", ephemeral=True)


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
