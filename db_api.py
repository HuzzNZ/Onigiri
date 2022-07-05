import datetime
import os
import random
import string
from typing import Union

import pymongo
import pytz
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


def sanitize_formatting(to_sanitize: str) -> str:
    characters_to_sanitize = [
        '\\', '`', '-', '=', '[', ']', '\'', ',', '.', '~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')',
        '_', '+', '{', '}', '|', ':', '"', '?', '/'
    ]
    new_string = ""
    for char in to_sanitize:
        if char in characters_to_sanitize:
            char = "\\" + char
        new_string += char
    return new_string


def make_datetime_jst(event):
    dt: datetime.datetime = event.get("datetime")
    if dt:
        event["datetime"] = dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Tokyo"))
    return event


class OnigiriDB:
    def __init__(self):
        self.client = MongoClient(
            f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASS')}"
            f"@onigiri.cal6d.mongodb.net/?retryWrites=true&w=majority")
        self.db = self.client["Onigiri-Fillings"]
        self.guilds = self.db["Guilds"]
        self.events = self.db["Events"]

    def check_guild_exists(self, guild_id):
        return self.guilds.find_one({"guild_id": guild_id}) or False

    def check_event_exists(self, guild_id, event_id):
        return self.events.find_one({"$and": [{"guild_id": guild_id}, {"event_id": event_id}]})

    def add_or_edit_guild(self, guild_id, schedule_channel_id, schedule_message_id, talent=None):
        current_guild = self.guilds.find_one({"guild_id": guild_id})
        new_talent = (talent or current_guild.get("talent", None)) if current_guild else talent
        new_guild = {
            "guild_id": guild_id,
            "schedule_channel_id": schedule_channel_id,
            "schedule_message_id": schedule_message_id,
            "talent": new_talent,
            "enabled": True
        }
        document = self.guilds.find_one_and_replace({"guild_id": guild_id}, new_guild)
        if not document:
            self.guilds.insert_one(new_guild)

    def edit_guild_talent(self, guild_id, talent_name):
        self.guilds.find_one_and_update({"guild_id": guild_id}, {"$set": {"talent": talent_name}})

    def edit_guild_editor(self, guild_id, editor_role_id=None):
        self.guilds.find_one_and_update({"guild_id": guild_id}, {"$set": {"editor_role_id": editor_role_id}})

    def edit_guild_description(self, guild_id, description=""):
        self.guilds.find_one_and_update({"guild_id": guild_id}, {"$set": {"description": description}})

    def disable_guild(self, guild_id):
        if self.guilds.find_one({"guild_id": guild_id}).get("enabled"):
            self.guilds.update_one({"guild_id": guild_id}, {"$set": {"enabled": False}})
            return True
        else:
            return False

    def enable_guild(self, guild_id):
        if not self.guilds.find_one({"guild_id": guild_id}).get("enabled"):
            self.guilds.update_one({"guild_id": guild_id}, {"$set": {"enabled": True}})
            return True
        else:
            return False

    def get_guild(self, guild_id):
        guild = self.check_guild_exists(guild_id)
        if not guild:
            return {}
        else:
            return guild

    def get_all_enabled_guilds(self):
        return [x for x in self.guilds.find({"enabled": True})]

    def get_guild_events(self, guild_id):
        return [make_datetime_jst(k) for k in self.events.find(
            {"guild_id": guild_id}, sort=[("datetime", pymongo.DESCENDING)])]

    def delete_guild(self, guild_id):
        self.guilds.delete_one({"guild_id": guild_id})

    def event_id_exists(self, guild_id, event_id):
        duplicate = [x for x in self.events.find({"$and": [{"guild_id": guild_id}, {"event_id": event_id}]})]
        return False if not duplicate else True

    def add_event(self, guild_id, title, event_type=0, url="", dt: Union[None, datetime.datetime] = None, conf=False):
        def get_event_id():
            return ''.join(random.choices(string.digits, k=4))

        event_id = get_event_id()
        while self.event_id_exists(guild_id, event_id):
            event_id = get_event_id()
        new_event = {
            "guild_id": guild_id,
            "event_id": event_id,
            "title": sanitize_formatting(title),
            "type": event_type,
            "url": url,
            "datetime": dt,
            "confirmed": conf,
            "stashed": False
        }
        self.events.insert_one(new_event)
        return event_id

    def edit_event(
            self, guild_id, event_id, title, event_type=0, url="",
            dt: Union[None, datetime.datetime] = None, conf=False, note=None):
        if not title:
            return False
        else:
            if note is None:
                prev_note = self.get_event(guild_id, event_id).get("note", "")
                note = prev_note
            edited_event = {
                "guild_id": guild_id,
                "event_id": event_id,
                "title": title,
                "type": event_type,
                "url": url,
                "datetime": dt,
                "confirmed": conf,
                "stashed": False,
                "note": note
            }
            self.events.replace_one({"$and": [{"guild_id": guild_id, "event_id": event_id}]}, edited_event)
        return event_id

    def get_event(self, guild_id, event_id):
        event = self.check_event_exists(guild_id, event_id)
        if not event:
            return {}
        else:
            return make_datetime_jst(event)

    def delete_event(self, guild_id, event_id):
        self.events.delete_one({"$and": [{"guild_id": guild_id, "event_id": event_id}]})

    def edit_event_title(self, guild_id, event_id, title: str):
        self.events.update_one(
            {"$and": [{"guild_id": guild_id, "event_id": event_id}]}, {"$set": {"title": sanitize_formatting(title)}})

    def edit_event_type(self, guild_id, event_id, event_type: int = 0):
        self.events.update_one(
            {"$and": [{"guild_id": guild_id, "event_id": event_id}]}, {"$set": {"type": event_type}})

    def edit_event_url(self, guild_id, event_id, url: str = ""):
        self.events.update_one(
            {"$and": [{"guild_id": guild_id, "event_id": event_id}]}, {"$set": {"url": url}})

    def edit_event_datetime(self, guild_id, event_id, dt: Union[None, datetime.datetime] = None):
        self.events.update_one(
            {"$and": [{"guild_id": guild_id, "event_id": event_id}]}, {"$set": {"datetime": dt}})

    def edit_event_confirmed(self, guild_id, event_id, conf: bool = False):
        self.events.update_one(
            {"$and": [{"guild_id": guild_id, "event_id": event_id}]}, {"$set": {"confirmed": conf}})

    def edit_event_stashed(self, guild_id, event_id, stashed: bool = False):
        self.events.update_one(
            {"$and": [{"guild_id": guild_id, "event_id": event_id}]}, {"$set": {"stashed": stashed}})

    def edit_event_note(self, guild_id, event_id, note: str = ""):
        self.events.update_one(
            {"$and": [{"guild_id": guild_id, "event_id": event_id}]}, {"$set": {"note": sanitize_formatting(note)}})


if __name__ == "__main__":
    db = OnigiriDB()
    print(db.event_id_exists(547571343986524180, "4ac8"))
