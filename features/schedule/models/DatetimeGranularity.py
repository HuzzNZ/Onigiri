from dataclasses import dataclass
from typing import TypeVar, Type

T = TypeVar("T")


@dataclass
class DatetimeGranularity:
    year: bool = False
    month: bool = False
    day: bool = False

    @classmethod
    def from_dict(cls: Type[T], d: dict) -> T:
        return cls(
            year=d.get("year", False),
            month=d.get("month", False),
            day=d.get("day", False)
        )

    def to_dict(self) -> dict:
        return {
            "year": self.year,
            "month": self.month,
            "day": self.day
        }
