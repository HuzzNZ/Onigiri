from dataclasses import dataclass
from typing import List, Type, TypeVar

T = TypeVar("T")


@dataclass
class GuildScheduleConfig:
    guild_id: int
    schedule_channel_id: int
    schedule_message_id_array: List[int]
    editor_role_id_array: List[int]
    enabled: bool = True
    talent: str = ""
    description: str = ""

    @classmethod
    def from_dict(cls: Type[T], d: dict) -> T:
        if d.get("schedule_message_ids"):
            schedule_message_id_array = d.get("schedule_message_ids")
        else:
            schedule_message_id_array = [d.get("schedule_message_id")] if d.get("schedule_message_id") else []

        if d.get("editor_role_ids"):
            editor_role_id_array = d.get("editor_role_ids")
        else:
            editor_role_id_array = [d.get("editor_role_id")] if d.get("editor_role_id") else []
        return cls(
            guild_id=d["guild_id"],
            schedule_channel_id=d["schedule_channel_id"],
            schedule_message_id_array=schedule_message_id_array,
            editor_role_id_array=editor_role_id_array,
            enabled=d.get("enabled", True),
            talent=d.get("talent", ""),
            description=d.get("description", "")
        )

    @classmethod
    def from_mongo(cls: Type[T], d: dict) -> T:
        return cls.from_dict(d)

    def to_dict(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "schedule_channel_id": self.schedule_channel_id,
            "schedule_message_ids": self.schedule_message_id_array,
            "editor_role_ids": self.editor_role_id_array,
            "enabled": self.enabled,
            "talent": self.talent,
            "description": self.description
        }
