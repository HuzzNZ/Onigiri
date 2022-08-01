from calendar import monthrange
from datetime import datetime, timedelta
from typing import Union

import pytz

from tools.constants import JST, MONTHS


def parse_date(date_str: str, g: bool = False) -> Union[datetime, None, dict]:
    """
    Parses a datetime given a date string.

    :param date_str: The date string to parse
    :param g: Optional flag to return a dict of the granularity of the date string.
    :return: Union[datetime, None, dict]
    """
    if not date_str and not g:
        return None

    date_str = date_str.lower()
    now = datetime.now(JST)
    year, month, day = 0, 0, 0

    if "today" in date_str:
        month = now.month
        day = now.day

    elif "tomorrow" in date_str:
        tomorrow = now + timedelta(days=1)
        year, month, day = tomorrow.year, tomorrow.month, tomorrow.day

    elif "/" in date_str:  # If in format [(YY)YY/]MM/DD
        dates = [int(x) for x in date_str.split("/")]

        # If in format MM/DD
        if len(dates) == 2:
            if 1 <= dates[0] <= 12:  # Only set month if MM between 1 and 12
                month = dates[0]
            if 1 <= dates[1] <= 31:  # Only set day if DD between 1 and 31
                day = dates[1]
            if not month or not day:
                raise ValueError

        # If in format (YY)YY/MM/DD
        elif len(dates) > 2:
            if 0 <= dates[0] <= 99:  # If the year is YY, and between (20)00 and (20)99
                year = 2000 + dates[0]
            elif 2000 <= dates[0] <= 2099:  # If the year is YYYY, and between 2000 and 2099
                year = dates[0]
            else:
                raise ValueError

            if 1 <= dates[1] <= 12:  # Only set month if MM between 1 and 12
                month = dates[1]
            if 1 <= dates[2] <= 31:  # Only set day if DD between 1 and 31
                day = dates[2]
            if not month or not day:
                raise ValueError

    else:  # If in any other format, like July 15, or 12 Sept
        dates = date_str.replace(",", " ").split(" ")
        for date in dates:  # Find the month
            if month:
                break
            for i in range(len(MONTHS)):
                if MONTHS[i] in date:
                    month = i + 1
                    break

        # Clean up numbers
        numbers = [x.strip("th").strip("st").strip("nd").strip("rd") for x in dates]
        numbers = [int(x) for x in numbers if x.isdigit()]
        for n in numbers:
            if 1 <= n <= 31 and not day:
                if month:
                    day = n
            elif 2000 <= n <= 2099:
                year = n

    if g:
        return {
            'year': True,
            'month': bool(month),
            'day': bool(day)
        }

    if not month:
        month = 12
    if not year:
        year = now.year
        if month < datetime.now(JST).month:
            year += 1
    if not day:
        day = monthrange(year, month)[1]

    return datetime(year, month, day, 14, 59, 59, 0).replace(tzinfo=pytz.utc).astimezone(JST)


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
