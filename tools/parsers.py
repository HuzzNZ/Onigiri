from datetime import datetime, timedelta
from typing import Union

import pytz

from tools.constants import JST, MONTHS


def parse_date(date_str: str) -> Union[datetime, None]:
    if not date_str:
        return None
    date_str = date_str.lower()
    now = datetime.now(JST)
    year, month, day = now.year, 0, 0
    using_current_year = True
    if "today" in date_str:
        month = now.month
        day = now.day
    elif "tomorrow" in date_str:
        tomorrow = now + timedelta(days=1)
        year, month, day = tomorrow.year, tomorrow.month, tomorrow.day
    if "/" in date_str:
        dates = date_str.split("/")
        if len(dates) == 2:
            if 0 < int(dates[0]) <= 12:
                month = int(dates[0])
            if 0 < int(dates[0]) <= 31:
                day = int(dates[1])
        elif len(dates) > 2:
            if int(dates[0]) < 100:
                year = 2000 + int(dates[0])
                using_current_year = False
            elif 3000 > int(dates[0]) > 2000:
                year = int(dates[0])
                using_current_year = False
            else:
                raise ValueError
            month = int(dates[1])
            day = int(dates[2])
    else:
        dates = date_str.replace(",", " ").split(" ")
        for date in dates:
            if not month:
                for i in range(len(MONTHS)):
                    if MONTHS[i] in date:
                        month = i + 1
                        break
        numbers = [int(x) for x in dates if x.isdigit()]
        for n in numbers:
            if 0 < n <= 31 and not day:
                day = n
            elif 3000 > n > 2000:
                year = n
                using_current_year = False

    if not month or not day:
        raise ValueError
    else:
        if using_current_year and month < datetime.now(JST).month:
            year += 1
        return datetime(year, month, day, 14, 59, 59, 0).replace(
            tzinfo=pytz.utc).astimezone(JST)


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
