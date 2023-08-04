from datetime import datetime
from typing import List

from features.schedule.models import GuildScheduleConfig, Event


def render_schedule(guild: GuildScheduleConfig, events: List[Event]) -> List[str]:
    content = []

    content += render_headline(guild)
    content += [""]
    content += render_past(...)
    content += [""]
    content += render_next_up(...)
    content += [""]
    content += render_future(...)

    return content


def render_headline(guild: GuildScheduleConfig) -> List[str]:
    content = []
    if guild.talent:
        talent_possessive = guild.talent + ("'" if guild.talent.endswith("s") else "'s")
        content.append(f"# __{talent_possessive}'s schedule__")
    else:
        content.append("# __An unnamed schedule__")
    content.append(f"(Events with timestamps are in your **local timezone**, and all other times are in **JST**.)")

    if guild.description:
        content.append("")
        content.append(f"> {guild.description}")

    content.append("")
    content.append(f"> Last refreshed <t:{int(datetime.now().timestamp())}:R>.")

    if not guild.enabled:
        content.append("> ⛔  *Currently disabled.*")

    return content


def render_past(past_events: List[Event]) -> List[str]:
    content = []

    ...

    return content


def render_next_up(next_event: Event) -> List[str]:
    content = []

    ...

    return content


def render_future(future_events: List[Event]) -> List[str]:
    content = []

    ...

    return content
