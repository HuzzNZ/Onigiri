from datetime import datetime
from typing import List, Tuple, Optional

from features.schedule.constants import JST, NONE, DD, DR, TR, EMOJIPEDIA, STASH, ED, YT_LOGO
from features.schedule.models import GuildScheduleConfig, Event

__all__ = ["render_schedule"]


def render_schedule(guild: GuildScheduleConfig, events: List[Event]) -> List[str]:
    content = []
    content += render_headline(guild)
    content += [""]
    if not events:
        content += ["**No events**. Use **`/schedule add`** to add some!"]
    else:
        past_events, next_event, future_events = classify_events(events)
        content += render_past(past_events)
        content += [""]
        if not next_event:
            content += ["**No future events**."]
        else:
            content += render_next_up(next_event)
            content += [DD if future_events else ""]
            content += render_future(future_events)
    return content


def render_headline(guild: GuildScheduleConfig) -> List[str]:
    content = []
    if guild.talent:
        talent_possessive = guild.talent + ("'" if guild.talent.endswith("s") else "'s")
        content.append(f"# __{talent_possessive} schedule__")
    else:
        content.append("# __An unnamed schedule__")
    content.append(f"(Events with timestamps are in your **local timezone**, and all other times are in **JST**.)")
    if guild.description:
        content.append("")
        content.append(f"> {guild.description}")
    content.append("")
    content.append(f"> Last refreshed <t:{int(datetime.now().timestamp())}:R>.")
    if not guild.enabled:
        content.append("> ⛔  **Currently disabled.**")
    return content


def render_past(past_events: List[Event]) -> List[str]:
    if not past_events:
        return ["**No past events**."]
    display_count = 3
    # total_past_events = len(past_events)
    past_events = past_events[-display_count:]  # Get last x events from list
    content = [
        f"## 🗂️  Past {len(past_events)} Event{'s' if len(past_events) != 1 else ''}  "
        # + (f"(See all {total_past_events} events with **`/history`**)" if total_past_events > display_count else "")
    ]
    for i, event in enumerate(past_events):
        is_last = i == len(past_events) - 1
        newline_prefix = f"{NONE if is_last else DD}{' ' * 14}"
        stash = "~~" if event.stashed else ""
        event_time_string, event_time_string_relative = format_event_time(event)
        title_no_backslash = event.title.replace("\\", "")
        title = event.title if not event.url else f'**[{title_no_backslash}](<{event.url}>)**'
        if event.url:
            title = title + "  🔗" if not ("youtu" in event.url and "be" in event.url) else title + f"  {YT_LOGO}"
        content.append(f"{DD}")
        content.append(
            f"{TR if is_last else DR}  ||`{event.event_id}`||  {EMOJIPEDIA[event.type]['past'] if not stash else STASH}"
            f"  **{stash}{event_time_string}"
            f"{('  ' + event_time_string_relative) if event_time_string_relative else ''}{stash}**"
        )
        content.append(f"{newline_prefix}{stash}{title}{stash}")
        if event.note:
            content.append(f"{newline_prefix}*({event.note})*")
    return content


def render_next_up(next_event: Event) -> List[str]:
    content = []
    newline_prefix = f"{DD}{' ' * 14}"
    stash = "~~" if next_event.stashed else ""
    emoji = EMOJIPEDIA[next_event.type].get("confirmed" if next_event.url else 'unconfirmed') if not stash else STASH
    event_time_string, event_time_string_relative = format_event_time(next_event)

    title_no_backslash = next_event.title.replace("\\", "")
    title = next_event.title if not next_event.url else f'**[{title_no_backslash}](<{next_event.url}>)**'
    if next_event.url:
        title = title + "  🔗" if not ("youtu" in next_event.url and "be" in next_event.url) else title + f"  {YT_LOGO}"

    content.append("## ⏰  Next Up")
    content.append(DD)
    content.append(
        f"{DR}  ||`{next_event.event_id}`||  {emoji}  "
        f"**{stash}{event_time_string}"
        f"{('  ' + event_time_string_relative) if event_time_string_relative else ''}{stash}**"
    )
    content.append(DD)
    content.append(f"{newline_prefix}{stash}{title}{stash}")
    if next_event.note:
        content.append(f"{newline_prefix}*({next_event.note})*")
    return content


def render_future(future_events: List[Event]) -> List[str]:
    if not future_events:
        return []
    content = ["☁️  **Upcoming**"]
    for event in future_events:
        newline_prefix = f"{DD}{' ' * 14}"
        stash = "~~" if event.stashed else ""
        emoji = (EMOJIPEDIA[event.type].get('confirmed' if event.url else 'unconfirmed')) if not stash else STASH
        event_time_string, event_time_string_relative = format_event_time(event)

        title_no_backslash = event.title.replace("\\", "")
        title = event.title if not event.url else f'**[{title_no_backslash}](<{event.url}>)**'
        if event.url:
            title = title + "  🔗" if not ("youtu" in event.url and "be" in event.url) else title + f"  {YT_LOGO}"

        content.append(DD)
        content.append(
            f"{DR}  ||`{event.event_id}`||  {emoji}  {stash}**{event_time_string}"
            f"{('  ' + event_time_string_relative) if event_time_string_relative else ''}**" +
            (f"  {title}" if not event_time_string_relative else '') + stash
        )
        if event_time_string_relative:
            content.append(f"{newline_prefix}{stash}{title}{stash}")
        if event.note:
            content.append(f"{newline_prefix}*({event.note})*")
    content.append(ED)
    return content


def classify_events(events: List[Event]) -> Tuple[List[Event], Optional[Event], List[Event]]:
    future_events: List[Event] = []
    past_events: List[Event] = []
    unspecified_events: List[Event] = []
    now = datetime.now(JST)
    for event in events:
        if event.datetime:
            (future_events if event.datetime > now else past_events).append(event)
        else:
            unspecified_events.append(event)
    past_events.sort(key=lambda e: e.datetime)
    future_events.sort(key=lambda e: e.datetime)
    future_events.extend(unspecified_events)
    next_event = None
    while not next_event and future_events:
        if future_events:
            n_event = future_events.pop(0)
            if n_event.stashed:
                past_events.append(n_event)
            else:
                next_event = n_event
    return past_events, next_event, future_events


def format_event_time(event: Event) -> Tuple[str, str]:
    if event.datetime:
        if not has_generic_date(event):
            return f"<t:{int(event.datetime.timestamp())}:f>", f"<t:{int(event.datetime.timestamp())}:R>"
        else:
            now = datetime.now(JST)
            base_str, time_format = "", ""
            # Day Specific
            if event.datetime_granularity.day:
                if event.datetime.year == now.year and \
                        event.datetime.month == now.month and event.datetime.day == now.day:
                    base_str = "Today"
                else:
                    time_format += "%b %e"  # Jan 1
                    if event.datetime.year != now.year and \
                            not (now.month == 12 and event.datetime.year - 1 == now.year):
                        time_format += ", %Y"  # Jan 1, 1990
            # Month Specific
            elif event.datetime_granularity.month:
                base_str += "◔  "
                time_format = "%B"  # January
                if event.datetime.year != now.year and not (now.month == 12 and event.datetime.year - 1 == now.year):
                    time_format += " %Y"  # January 1990
            # Year Specific
            elif event.datetime_granularity.year:
                base_str += "◕  "
                time_format += "%Y"  # 1990
            return base_str + event.datetime.strftime(time_format), ""
    else:
        return "Unknown", ""


def has_generic_date(event: Event) -> bool:
    if event.datetime:
        return event.datetime.hour == 23 and event.datetime.minute == 59 and event.datetime.second == 59
    else:
        return True
