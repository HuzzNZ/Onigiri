import datetime
from dataclasses import dataclass
from typing import Literal, Optional, TypeVar, Type

import pytz

from features.schedule.constants import JST
from features.schedule.models import DatetimeGranularity

T = TypeVar('T')


@dataclass
class Event:
    guild_id: int
    event_id: str
    title: str
    datetime: Optional[datetime.datetime]
    datetime_granularity: DatetimeGranularity = DatetimeGranularity()
    type: Literal[0, 1, 2, 3, 4] = 0
    stashed: bool = False
    url: str = ""
    note: str = ""

    @classmethod
    def from_dict(cls: Type[T], d: dict) -> T:
        return cls(
            guild_id=d["guild_id"],
            event_id=d["event_id"],
            title=d["title"],
            datetime=d.get("datetime"),
            datetime_granularity=DatetimeGranularity.from_dict(d.get("datetime_granularity", {})),
            type=d.get("type", 0),
            stashed=d.get("stashed", False),
            url=d.get("url", ""),
            note=d.get("note", "")
        )

    @classmethod
    def from_mongo(cls: Type[T], d: dict) -> T:
        event = cls.from_dict(d)
        event.datetime = utc_as_jst(event.datetime)
        return event

    def to_dict(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "event_id": self.event_id,
            "title": self.title,
            "datetime": self.datetime,
            "datetime_granularity": self.datetime_granularity.to_dict(),
            "type": self.type,
            "stashed": self.stashed,
            "url": self.url,
            "note": self.note
        }


def utc_as_jst(dt: Optional[datetime.datetime]) -> Optional[datetime.datetime]:
    if dt:
        return dt.replace(tzinfo=pytz.utc).astimezone(JST)
    else:
        return None
