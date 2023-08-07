from functools import wraps

import discord

from exceptions import InvalidArgument
from features.schedule.database import ScheduleDB
from features.schedule.util import parse_date, parse_time


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
                raise InvalidArgument(F"No event with ID \"{event_id}\" was found.")

        # Validate date / time
        time_capable = False
        parsed_date = None
        if event:
            time_capable = event.datetime_granularity.day
            parsed_date = event.datetime
        if kwargs.get("date", ""):
            date = kwargs["date"]
            if event:
                new_parsed_date, new_parsed_date_granularity = parse_date(date)
                time_capable = event.datetime and (event.datetime_granularity.day or new_parsed_date_granularity.day)
                parsed_date = new_parsed_date or event.datetime
            else:
                try:
                    parsed_date, parsed_date_granularity = parse_date(date)
                except ValueError:
                    raise InvalidArgument(f"Bad date input. \"{date}\" was not able to be parsed as a date.")
                time_capable = parsed_date_granularity.day
        if kwargs.get("time", ""):
            if not time_capable:
                raise InvalidArgument(f"Event does not have an associated date. Set a date before setting a time.")
            time = kwargs["time"]
            try:
                parse_time(time, parsed_date)
            except ValueError:
                raise InvalidArgument(f"Bad time input. \"{time}\" was not able to be parsed as a time.")

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

        if kwargs.get("talent", ""):
            talent = kwargs["talent"]
            if len(talent) > 30:
                raise InvalidArgument(f"Talent name too long. Max 30 characters (Currently {len(talent)}).")
            kwargs["note"] = sanitize_formatting(talent)

        if kwargs.get("description", ""):
            description = kwargs["description"]
            if len(description) > 200:
                raise InvalidArgument(f"Description too long. Max 200 characters (Currently {len(description)}).")
            kwargs["note"] = sanitize_formatting(description)

        # Validate url
        if kwargs.get("url", ""):
            url: str = kwargs["url"]
            if not (url.startswith("http://") or url.startswith("https://")):
                raise InvalidArgument(f"Invalid URL. URLs should begin with \"http://\" or \"https://\".")

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
