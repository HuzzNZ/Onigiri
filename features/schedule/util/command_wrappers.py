from functools import wraps

import discord
from discord.ui import View, button

from api.youtube import YouTube, YouTubeURL
from exceptions import InvalidArgument
from features.schedule.constants import YT, CANCELLED
from features.schedule.database import ScheduleDB
from features.schedule.models import DatetimeGranularity, Event
from features.schedule.util.datetime_parsers import parse_date, parse_time, parse_type
from tools.constants import YES


def validate_arguments(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        interaction = None
        schedule_cog = None
        for arg in args:
            if isinstance(arg, discord.Interaction):
                interaction = arg
                break
        for arg in args:
            from features.schedule.cog import Schedule
            if isinstance(arg, Schedule):
                schedule_cog = arg

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
            try:
                yt = YouTube(YouTubeURL.unsafe(url))

                class YouTubeConfirmation(View):
                    def __init__(self):
                        super().__init__(timeout=120)
                        self.use_all = None

                    @button(label='Use all', style=discord.ButtonStyle.blurple)
                    async def delete(self, *_):
                        self.use_all = True
                        self.stop()

                    @button(label='Use URL only', style=discord.ButtonStyle.secondary)
                    async def cancel(self, *_):
                        self.use_all = False
                        self.stop()

                view = YouTubeConfirmation()
                yt_title = yt.title[:24] + "..." if len(yt.title) > 27 else yt.title
                title = (yt_title if not kwargs.get('title') else kwargs.get('title')) if not event else event.title
                note = ("" if not kwargs.get("note") else kwargs.get("note")) if not event else event.note
                url = yt.url.get_short_url()
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message(
                    f"## {YT}  YouTube video found.\n** **\n**Would you like to " +
                    (f"edit event `{event.event_id}`" if event else "create the event") +
                    f" using the following details?**\n"
                    f"- **Timestamp**: <t:{int(yt.start_time.timestamp())}:f>  <t:{int(yt.start_time.timestamp())}:R>\n"
                    f"- **Title**: {title}\n" +
                    (f"- **Note**: {note}\n" if note else "") + f"- **URL**: {url}\n"
                                                                f"- **Type**: `{yt.content_type}`\n",
                    view=view, ephemeral=True
                )
                timeout = await view.wait()
                if not timeout:
                    kwargs["url"] = url
                    if view.use_all:
                        dt_g = DatetimeGranularity(True, True, True)
                        db = ScheduleDB()
                        new_event = Event(
                            guild_id=interaction.guild.id,
                            event_id=event.event_id if event else await db.get_available_event_id(interaction.guild.id),
                            title=title,
                            datetime=yt.start_time,
                            datetime_granularity=dt_g,
                            type=parse_type(yt.content_type),
                            note=note,
                            url=url
                        )
                        if event:
                            await db.update_event(new_event)
                            await interaction.edit_original_response(
                                content=f"{YES}**Event `{event.event_id}` updated**.", view=None
                            )
                        else:
                            event = await db.create_event(new_event)
                            await interaction.edit_original_response(
                                content=f"{YES}**Event `{event.event_id}` created**.", view=None
                            )
                        await schedule_cog.update_schedule_messages(interaction.guild.id)
                        return
                    else:
                        await interaction.edit_original_response(content="** **", view=None)
                else:
                    await interaction.edit_original_response(content=f"{CANCELLED}**Timed out.**", view=None)
            except ValueError:
                pass
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
