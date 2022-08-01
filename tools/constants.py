import pytz
import logging

DD = "<:dd:992623483563561030>"
DR = "<:dr:992624464078585916>"
TR = "<:tr:992625824140361728>"
ED = "<:ed:992627365102485624>"
YES = "✅  "
NO = "❌  "
NONE = "      "
YT = "▶️"
STASHED = "❌"
WARNING = "⚠️"
CANCELLED = "🚫"
JST = pytz.timezone("Asia/Tokyo")
MONTHS = ["jan", 'feb', "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
EVENT_ID_DESC = "The 4-digit numeric ID associated with each event. (e.g. 1902, 6817, etc.)"
EVENT_TYPES = ['stream', 'video', 'event', 'release', 'other']
YR = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=" \
     r"|embed\/|v\/)?)([\w\-]+)(\S+)?$"
DEFAULT_DT_G = {
    'year': True, 'month': True, 'day': True
}

LOG_HANDLER = logging.StreamHandler()
fmt = logging.Formatter(
    '%(asctime)s [%(levelname)-8s] onigiri: %(message)s',
    "[%Y-%m-%d %H:%M:%S]"
)
LOG_HANDLER.setFormatter(fmt)

EMOJIPEDIA = [
    {
        "past": "✅",
        "confirmed": "▶️",
        "unconfirmed": "💭"
    },
    {
        "past": "🎞️",
        "confirmed": "🎞️",
        "unconfirmed": "🎞️"
    },
    {
        "past": "🎆",
        "confirmed": "🎆",
        "unconfirmed": "🎆"
    },
    {
        "past": "💿",
        "confirmed": "💿",
        "unconfirmed": "💿"
    },
    {
        "past": "✅",
        "confirmed": "▶️",
        "unconfirmed": "💭"
    },
]
