import datetime
import random
import string
from typing import Optional, Literal, List

import pymongo

from database import MongoSingleton
from features.schedule.models import Event, DatetimeGranularity, GuildScheduleConfig
from .AbstractScheduleDB import AbstractScheduleDB


class ScheduleDB(AbstractScheduleDB):
    def __init__(self):
        self.db = MongoSingleton.conn().client
        self.guilds = self.db["Onigiri-Fillings"]["Guilds"]
        self.events = self.db["Onigiri-Fillings"]["Events"]

    async def get_guild_exists(self, guild_id: int) -> bool:
        return bool(self.guilds.find_one({'guild_id': guild_id}))

    async def get_available_event_id(self, guild_id) -> str:
        event_id = None
        while not event_id:
            new_id = ''.join(random.choices(string.digits, k=4))
            if not await self.get_event_exists(guild_id, new_id):
                event_id = new_id
        return event_id

    async def get_event_exists(self, guild_id, event_id: str) -> bool:
        return bool(self.events.find_one({"$and": [{"guild_id": guild_id}, {"event_id": event_id}]}))

    async def get_guild(self, guild_id: int) -> Optional[GuildScheduleConfig]:
        guild = self.guilds.find_one({'guild_id': guild_id})
        if not guild:
            return None
        else:
            return GuildScheduleConfig.from_mongo(guild)

    async def get_all_guilds(self) -> List[GuildScheduleConfig]:
        return [GuildScheduleConfig.from_mongo(x) for x in self.guilds.find()]

    async def get_enabled_guilds(self) -> List[GuildScheduleConfig]:
        return [GuildScheduleConfig.from_mongo(x) for x in self.guilds.find({"enabled": True})]

    async def get_event(self, guild_id: int, event_id: str) -> Optional[Event]:
        event = self.events.find_one({"$and": [{"guild_id": guild_id}, {"event_id": event_id}]})
        if event:
            return Event.from_mongo(event)
        else:
            return None

    async def get_all_events(self, guild_id: int) -> List[Event]:
        return [Event.from_mongo(k) for k in self.events.find(sort=[
            ("datetime", pymongo.DESCENDING),
            ('datetime_granularity', pymongo.ASCENDING),
            ('note', pymongo.DESCENDING)
        ])]

    async def get_guild_events(self, guild_id: int) -> List[Event]:
        return [Event.from_mongo(k) for k in self.events.find(
            {"guild_id": guild_id},
            sort=[
                ("datetime", pymongo.DESCENDING),
                ('datetime_granularity', pymongo.ASCENDING),
                ('note', pymongo.DESCENDING)
            ]
        )]

    async def create_guild(self, guild: GuildScheduleConfig) -> GuildScheduleConfig:
        self.guilds.insert_one(guild.to_dict())
        return guild

    async def create_event(self, event: Event) -> Event:
        self.events.insert_one(event.to_dict())
        return event

    async def update_guild(self, guild: GuildScheduleConfig) -> GuildScheduleConfig:
        self.guilds.replace_one({"guild_id": guild.guild_id}, guild.to_dict())
        return guild

    async def update_event(self, event: Event) -> Event:
        self.events.replace_one({"$and": [{"guild_id": event.guild_id, "event_id": event.event_id}]}, event.to_dict())
        return event

    async def delete_guild(self, guild_id: int) -> None:
        self.guilds.delete_one({"guild_id": guild_id})

    async def delete_event(self, guild_id: int, event_id: str) -> None:
        self.events.delete_one({"$and": [{"guild_id": guild_id, "event_id": event_id}]})

    async def set_guild_enable(self, guild_id: int) -> None:
        self.guilds.find_one_and_update({"guild_id": guild_id}, {"$set": {"enabled": True}})

    async def set_guild_disable(self, guild_id: int) -> None:
        self.guilds.find_one_and_update({"guild_id": guild_id}, {"$set": {"enabled": False}})

    async def set_guild_talent(self, guild_id: int, talent: str) -> None:
        self.guilds.find_one_and_update({"guild_id": guild_id}, {"$set": {"talent": talent}})

    async def set_guild_description(self, guild_id: int, description: str) -> None:
        self.guilds.find_one_and_update({"guild_id": guild_id}, {"$set": {"description": description}})

    async def set_guild_channel(self, guild_id: int, schedule_channel: int) -> None:
        self.guilds.find_one_and_update(
            {"guild_id": guild_id},
            {"$set": {"schedule_channel_id": schedule_channel}}
        )

    async def set_guild_messages(self, guild_id: int, schedule_messages: List[int]) -> None:
        self.guilds.find_one_and_update(
            {"guild_id": guild_id},
            {"$set": {"schedule_message_ids": schedule_messages}}
        )

    async def set_guild_editors(self, guild_id: int, editors: List[int]) -> None:
        self.guilds.find_one_and_update(
            {"guild_id": guild_id},
            {"$set": {"editor_role_ids": editors}}
        )

    async def set_event_title(self, guild_id: int, event_id: str, title: str) -> None:
        self.events.find_one_and_update(
            {'$and': [{"guild_id": guild_id, "event_id": event_id}]},
            {"$set": {"title": title}}
        )

    async def set_event_datetime(self, guild_id: int, event_id: str, dt: Optional[datetime.datetime]) -> None:
        self.events.find_one_and_update(
            {'$and': [{"guild_id": guild_id, "event_id": event_id}]},
            {"$set": {"datetime": dt}}
        )

    async def set_event_datetime_granularity(self, guild_id: int, event_id: str, dt_g: DatetimeGranularity) -> None:
        self.events.find_one_and_update(
            {'$and': [{"guild_id": guild_id, "event_id": event_id}]},
            {"$set": {"datetime_granularity": dt_g.to_dict()}}
        )

    async def set_event_type(self, guild_id: int, event_id: str, t: Literal[0, 1, 2, 3, 4]) -> None:
        self.events.find_one_and_update(
            {'$and': [{"guild_id": guild_id, "event_id": event_id}]},
            {"$set": {"type": t}}
        )

    async def set_event_stashed(self, guild_id: int, event_id: str, stashed: bool) -> None:
        self.events.find_one_and_update(
            {'$and': [{"guild_id": guild_id, "event_id": event_id}]},
            {"$set": {"stashed": stashed}}
        )

    async def set_event_url(self, guild_id: int, event_id: str, url: str) -> None:
        self.events.find_one_and_update(
            {'$and': [{"guild_id": guild_id, "event_id": event_id}]},
            {"$set": {"url": url}}
        )

    async def set_event_note(self, guild_id: int, event_id: str, note: str) -> None:
        self.events.find_one_and_update(
            {'$and': [{"guild_id": guild_id, "event_id": event_id}]},
            {"$set": {"note": note}}
        )
