from datetime import datetime
from .constants import *


def is_generic_date(dt: datetime) -> bool:
    """
    Checks if a given datetime is a generic date based on whether the time is 23:59:59.

    :param dt: The datetime to check
    :return: True if the time is 23:59:59, False if not
    """
    if dt:
        return dt.hour == 23 and dt.minute == 59 and dt.second == 59


def will_use_timestamp(event: dict) -> bool:
    """
    Checks if a given event should be displayed with a Discord timestamp.

    :param event: The event to check
    :return: True if the event should be displayed with a Discord timestamp, False if not
    """
    dt: datetime = event.get("datetime")
    return event.get("confirmed") or (event.get('type') == 2 and not is_generic_date(dt))


def format_event_time(event: dict, relative: bool = False) -> str:
    """
    Formats the time displayed next to an event.

    :param event: The event to format
    :param relative: If the Discord timestamp should be relative
    :return: A string representing the datetime of an event
    """
    dt: datetime = event.get("datetime")
    if dt:
        if will_use_timestamp(event):
            return f"<t:{int(dt.timestamp())}:{'R' if relative else 'f'}>"
        else:
            now = datetime.now(JST)
            dt_g = event.get("datetime_granularity", DEFAULT_DT_G)
            base_str, time_format = "", ""
            if dt_g.get("day"):
                if dt.year == now.year and dt.month == now.month and dt.day == now.day:
                    base_str = "Today"
                    time_format += ""
                else:
                    base_str = ""
                    time_format += "%b %-d"
                if dt.year != now.year and not (now.month == 12 and dt.year - 1 == now.year):
                    time_format += ", %Y"
                if not is_generic_date(dt):
                    time_format += f"{',' if base_str else ' '} %H:%M"
            elif dt_g.get("month"):
                base_str += "◔  "
                time_format = "%B"
                if dt.year != now.year and not (now.month == 12 and dt.year - 1 == now.year):
                    time_format += " %Y"
            elif dt_g.get("year"):
                base_str += "◕  "
                time_format += "%Y"
            return base_str + dt.strftime(time_format)
    else:
        return "Unknown"


def get_headline(talent: str = ""):
    """
    Gets the headline of a schedule.
    :param talent: The name of the talent the schedule is for
    :return: A string of a formatted headline
    """
    if talent:
        talent_name_with_possessive = talent + ("'" if talent.endswith("s") else "'s")
        headline = f'__**{talent_name_with_possessive} unofficial schedule**__'
    else:
        headline = "__**A schedule**__:"
    return headline + "\n(Events with Discord Timestamps are in your **local timezone**," \
                      f" all other times are in **JST**.)"


def separate_events(event_list: list) -> (list, list, list):
    """
    Separates a list of events into the past, future and unspecified.

    :param event_list: The list of events to separate
    :return: Three lists of events, past_list, future_list and unspecified_list
    """
    future_list = []
    past_list = []
    unspecified_list = []

    time_now = datetime.now(JST)

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


def is_on_same_day(e1: dict, e2: dict) -> bool:
    """
    Checks if two events occur on the same day. Will return false if the granularity of each event
    do not match up.
    """
    dt1, dt2 = e1.get("datetime"), e2.get("datetime")
    dt_g1 = e1.get("datetime_granularity", DEFAULT_DT_G)
    dt_g2 = e2.get("datetime_granularity", DEFAULT_DT_G)
    if not dt1 and not dt2:
        return True
    if not dt1 or not dt2:
        return False
    if dt_g1 != dt_g2:
        return False
    return dt1.year == dt2.year and dt1.month == dt2.month and dt1.day == dt2.day


def render_history_events(events: [dict]) -> [str]:
    if not events:
        return []
    contents = []
    for event in events:
        s = "~~" if event.get("stashed") else ""
        line = f"||`{event.get('event_id')}`|| "
        if event.get("datetime"):
            past = event.get("datetime") <= datetime.now(JST)
        else:
            past = False
        emoji = STASHED if s else EMOJIPEDIA[event.get('type')].get(
            'past' if past else 'confirmed' if event.get('confirmed') else 'unconfirmed')
        line += emoji + " "
        line += f"{s}**{format_event_time(event)}** - "
        if event.get('url'):
            line += '['
        line += f"{event.get('title')}"
        if event.get('url'):
            line += f"]({event.get('url')})"
        line += s

        contents.append(line)
    return contents


def render_past_events(past_list: [dict], amount: int = 0) -> [str]:
    """
    Renders the "Past Events" section of the schedule.

    :param past_list: A list of events representing past events in descending order.
    :param amount: The amount of events to display. Defaults to 0 (unlimited).
    :return: A formatted list of strings representing past events.
    """
    if not past_list:
        return []

    total_length = len(past_list)
    past_list = past_list[:amount][::-1]
    contents = [
        f"🗂️  __**Past {min(amount, len(past_list))} Event{'s' if len(past_list) != 1 else ''}**__ "
        f" (See all {total_length} events with **`/history`**)"]

    for i in range(len(past_list)):
        event = past_list[i]
        is_last = i == len(past_list) - 1
        nl_prefix = f"{NONE if is_last else DD}{' ' * 15}"
        s = "~~" if event.get("stashed") else ""

        contents.append(f"{DD}")
        contents.append(
            f"{TR if is_last else DR}  ||`{event.get('event_id')}`||  "
            f"{EMOJIPEDIA[event.get('type')].get('past') if not s else STASHED}  "
            f"**{s}{format_event_time(event)}{s}**")

        contents.append(f"{nl_prefix}{s}{event.get('title')}{s}")
        if event.get("url"):
            contents.append(f"{nl_prefix}{s}<{event.get('url')}>{s}")
        if event.get("note"):
            contents.append(f"{nl_prefix}*({event.get('note')})*")
    return contents


def render_next_up(event: dict) -> [str]:
    """
    Renders the "Next Up" section of the schedule.

    :param event: The event that is next up.
    :return: A formatted list of strings representing the next up event.
    """
    if not event:
        return []

    nl_prefix = f"{DD}{' ' * 15}"
    s = "~~" if event.get("stashed") else ""

    emoji = EMOJIPEDIA[event.get('type')].get(
        'confirmed' if event.get('confirmed') else 'unconfirmed') if not s else STASHED

    contents = [
        f"⏰  __**Next Up**__",
        f"{DD}",
        f"{DR}  ||`{event.get('event_id')}`||   {emoji}  **{s}{format_event_time(event)}{s}**"
    ]

    if will_use_timestamp(event):
        contents.append(f"{DD}")
    contents.append(f"{nl_prefix}**{s}{event.get('title')}{s}**")

    if event.get('url'):
        contents.append(f"{nl_prefix}{s}<{event.get('url')}>{s}")
    if will_use_timestamp(event):
        contents.append(f"{nl_prefix}{s}{format_event_time(event, True)}{s}")
    if event.get("note"):
        contents.append(f"{nl_prefix}*({event.get('note')})*")

    return contents


def render_future(future_list: [dict]) -> [str]:
    """
    Renders the "Upcoming" section of the schedule.

    :param future_list: A list of events representing upcoming events.
    :return: A formatted list of strings representing the upcoming events.
    """
    if not future_list:
        return []

    contents = [f"☁️  __**Upcoming**__"]
    previous_event = {}
    for event in future_list:
        uses_timestamp = will_use_timestamp(event)
        nl_prefix = f"{DD}{' ' * 15}"
        s = "~~" if event.get("stashed") else ""

        emoji = (EMOJIPEDIA[event.get('type')].get(
            'confirmed' if event.get('confirmed') else 'unconfirmed')) if not s else STASHED

        if not is_on_same_day(previous_event, event) or previous_event.get("note"):
            contents.append(f"{DD}")

        contents.append(
            f"{DR}  ||`{event.get('event_id')}`||   {emoji}  "
            f"{s}**{format_event_time(event)}**"
            f"{('  ' + event.get('title')) if not uses_timestamp else ''}{s}")

        if uses_timestamp:
            contents.append(f"{nl_prefix}{s}{event.get('title')}{s}")
        if event.get("url"):
            contents.append(f"{nl_prefix}{s}<{event.get('url')}>{s}")
        if event.get("note"):
            contents.append(f"{nl_prefix}*({event.get('note')})*")
        previous_event = event

    contents.append(f"{ED}")
    return contents
