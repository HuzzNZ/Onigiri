from functools import wraps
from typing import List

import discord
from discord import app_commands

from features.schedule.database import ScheduleDB
from exceptions import InvalidArgument
from features.schedule.util import parse_date, parse_time


async def type_autocomplete(_, current: str) -> List[app_commands.Choice[str]]:
    """
    Autocomplete for event types.
    """
    types = ['stream', 'video', 'event', 'release', 'other']
    choices = []
    for i in range(len(types)):
        if current.lower() in types[i]:
            choices.append(app_commands.Choice(name=types[i], value=types[i]))
    return choices


# Check Decorators


def guild_registered():
    def predicate(interaction: discord.Interaction) -> bool:
        return True  # TODO

    return app_commands.check(predicate)


def author_is_editor():
    def predicate(interaction: discord.Interaction) -> bool:
        return True  # TODO

    return app_commands.check(predicate)


def author_is_admin():
    def predicate(interaction: discord.Interaction) -> bool:
        return True  # TODO

    return app_commands.check(predicate)


def validate_arguments(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        interaction = None
        for arg in args:
            if isinstance(arg, discord.Interaction):
                interaction = arg
                break
        assert isinstance(interaction, discord.Interaction)

        db = ScheduleDB()
        event = None

        # Validate event_id exists
        if kwargs.get("event_id", ""):
            event_id = kwargs["event_id"]
            event = await db.get_event(interaction.guild.id, event_id)
            if not event:
                raise InvalidArgument(F"No event with ID `{event_id}` was found.")

        # Validate date / time
        time_capable = False
        parsed_date = None
        if kwargs.get("date", ""):
            date = kwargs["date"]
            if event:
                time_capable = event.datetime and event.datetime_granularity.day
                parsed_date = event.datetime
            else:
                try:
                    parsed_date, parsed_date_granularity = parse_date(date)
                except ValueError:
                    raise InvalidArgument(f"Bad date input. `{date}` was not able to be parsed as a date.")
                time_capable = parsed_date_granularity.day
        if kwargs.get("time", ""):
            if not time_capable:
                raise InvalidArgument(f"Event does not have an associated date. Set a date before setting a time.")
            time = kwargs["time"]
            try:
                parse_time(time, parsed_date)
            except ValueError:
                raise InvalidArgument(f"Bad time input. `{time}` was not able to be parsed as a time.")

        # Validate title shorter than 30 characters, sanitize formatting
        if kwargs.get("title", ""):
            title = kwargs["title"]
            if len(title) > 30:
                raise InvalidArgument(f"Title too long. Max 30 characters (Currently {len(title)}).")
            kwargs["title"] = sanitize_formatting(title)

        # Validate note shorter than 30 characters, sanitize formatting
        if kwargs.get("note", ""):
            note = kwargs["note"]
            if len(note) > 30:
                raise InvalidArgument(f"Note too long. Max 30 characters (Currently {len(note)}).")
            kwargs["note"] = sanitize_formatting(note)

        # Validate url
        if kwargs.get("url", ""):
            url: str = kwargs["url"]
            if not (url.startswith("http://") or url.startswith("https://")):
                raise InvalidArgument(f"Invalid URL. URLs should begin with `http://` or `https://`.")

        return await func(*args, **kwargs)

    return wrapper


def sanitize_formatting(to_sanitize: str) -> str:
    characters_to_sanitize = [
        '\\', '`', '-', '=', '[', ']', '\'', ',', '.', '~', '!', '@', '#', '$', '%', '^', '&', '*',
        '(', ')', '_', '+', '{', '}', '|', ':', '"', '?', '/'
    ]
    new_string = ""
    for char in to_sanitize:
        if char in characters_to_sanitize:
            char = "\\" + char
        new_string += char
    return new_string
