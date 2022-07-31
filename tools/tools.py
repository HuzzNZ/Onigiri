from typing import Optional
from datetime import datetime
import re
from .constants import YR

from .constants import DD, ED
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


def render_schedule(guild: dict, events: [dict]) -> str:
    """
    Returns a rendered string of a guild's schedule.
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

    content = "\n".join(content_list)
    return content
