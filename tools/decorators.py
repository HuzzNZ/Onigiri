import asyncio
from functools import wraps

import discord

from apis.youtube_api import YouTubeURL
from .tools import validate_yt
from .constants import YES, CANCELLED, EVENT_TYPES, YT
from .exceptions import GuildNotRegistered, GuildNotEnabled, MessageUnreachable, BadInput
from .parsers import parse_time, parse_date
from .views import PopulateFromURLView


def check_general(func):
    """
    A decorator that checks general bot permissions, and guild data. Checks include:
        - Check if guild is registered in DB
        - Check if guild is enabled
        - Check if schedule message is reachable

    :param func: The function that the decorator wraps around
    :return: The return value of the function
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            interaction: discord.Interaction = args[0]
            guild = interaction.client.db.check_guild_exists(interaction.guild.id)
        except AttributeError:
            interaction: discord.Interaction = args[1]
            guild = interaction.client.db.check_guild_exists(interaction.guild.id)

        # Check guild is registered in DB
        if not guild:
            raise GuildNotRegistered

        # Check guild is enabled
        if guild.get('enabled') is False:
            raise GuildNotEnabled

        # Check schedule message is reachable
        current_channel = guild.get("schedule_channel_id")
        current_message = guild.get("schedule_message_id")
        try:
            await interaction.client.get_channel(current_channel).fetch_message(current_message)
        except (discord.NotFound, discord.Forbidden, AttributeError):
            raise MessageUnreachable

        return await func(*args, **kwargs)

    return wrapper


def check_event_id(func):
    """
    A decorator that checks the `event_id` parameter in the command.

    :param func: The function that the decorator wraps around
    :return: The return value of the function
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        interaction: discord.Interaction = args[0]
        event_id = kwargs.get("event_id")[:4]
        event = interaction.client.db.check_event_exists(interaction.guild.id, event_id)

        if not event:  # Check if event with that ID exists
            raise BadInput(f"**No event with ID `{event_id}` found!**")
        kwargs["event_id"] = event_id
        return await func(*args, **kwargs)

    return wrapper


def check_date_time(func):
    """
    A decorator that checks the `date` and `time` parameters in the command.

    :param func: The function that the decorator wraps around
    :return: The return value of the function
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        interaction: discord.Interaction = args[0]
        current_datetime = interaction.client.db.get_guild(interaction.guild.id).get("datetime")

        date: str = kwargs.get("date", "")
        time: str = kwargs.get("time", "")

        if time and (not current_datetime and not date):  # Check if a date is/will be set
            raise BadInput(f"**No date set on event!** Please add a date before adding a time.")

        if date:  # Check date input
            try:
                current_datetime = parse_date(date)
            except ValueError:
                raise BadInput(f"**Bad date input.** Please check your input for errors.")

        if time:  # Check time input
            try:
                parse_time(time, current_datetime)
            except ValueError:
                raise BadInput(f"**Bad time input.** Please check your input for errors.")
        return await func(*args, **kwargs)

    return wrapper


def check_title(func):
    """
    A decorator that checks the `title` parameter in the command. Checks include:
        - Check if `title` is under 30 characters

    :param func: The function that the decorator wraps around
    :return: The return value of the function
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        title: str = kwargs.get("title", "")
        if title is not None:
            if len(title) > 30:
                raise BadInput(f"**Title too long!** Max 30 characters. (Currently {len(title)})")
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
                raise BadInput("**Invalid URL!** URLs should begin with `http://` or `https://`.")
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
