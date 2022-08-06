from typing import Optional, List
from datetime import datetime
import re

import discord
from discord import app_commands

from .constants import YR, DD, ED
from .helpers import \
    get_headline, separate_events, render_past_events, render_next_up, render_future


def validate_yt(link: str) -> Optional[str]:
    """
    Validates a YouTube link against a regex string, and returns the YouTube ID if there is a match.

    :param link: The link to be verified
    :return: The YouTube ID from the link, if it exists
    """
    yt_id = None
    if match := re.search(YR, link, re.IGNORECASE):
        yt_id = match.group(6)
    return yt_id


def log_time() -> str:
    """
    Returns a string representing the current time.

    :return: String representing the current time
    """
    return datetime.now().strftime('[%b %d %H:%M:%S]  ')


def render_schedule(guild: dict, events: [dict]) -> list:
    """
    Returns a rendered list of lines of a guild's schedule.
    :param guild:
    :param events:
    :return:
    """
    talent_name: str = guild.get("talent")
    content_list = [get_headline(talent_name), ""]

    if guild.get("description"):
        content_list += [f"> {guild.get('description')}"]
        content_list += [""] if guild.get("enabled") else ["> ⛔  *Currently disabled.*", ""]

    content_list += [f"> *Last refreshed <t:{int(datetime.now().timestamp())}:R>.*", ""]

    if events:
        past, future, unspecified = separate_events(events)
        if past:
            content_list += [f'> ***{len(past)}** events in history.*']
            content_list += [""]

        future = future[::-1] + unspecified

        if future:
            content_list += render_next_up(future[0])
            if len(future) > 1:
                content_list += [f"{DD}"]
                content_list += render_future(future[1:])
            else:
                content_list += [f"{ED}"]
        else:
            content_list += [
                "> *Nothing planned in the future. "
                "Use **/add**, or **/add-yt** to add some events!*"]
    else:
        content_list += ["> *No events. Use **/add**, or **/add-yt** to add some events!*"]

    return content_list


async def type_ac(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """
    Autocomplete for types.
    """
    types = ['stream', 'video', 'event', 'release', 'other']
    choices = []
    for i in range(len(types)):
        if current.lower() in types[i]:
            choices.append(app_commands.Choice(name=types[i], value=types[i]))
    return choices
