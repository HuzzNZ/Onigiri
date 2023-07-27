import os
from typing import TypeVar, Type

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

T = TypeVar("T")


class MongoSingleton:
    _instance = None
    _singleton_key = "77fwNHWihaAMpccNKrRUVmDvEWhOHj1o"

    @classmethod
    def conn(cls: Type[T]) -> T:
        if cls._instance and isinstance(cls._instance, MongoSingleton):
            return cls._instance
        else:
            cls._instance = cls(singleton_key=cls._singleton_key)
            return cls._instance

    def __init__(self, **kwargs):
        if kwargs.get("singleton_key", "") == "77fwNHWihaAMpccNKrRUVmDvEWhOHj1o":
            self.client = MongoClient(
                f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASS')}"
                f"@onigiri.cal6d.mongodb.net/?retryWrites=true&w=majority"
            )
        else:
            raise ValueError("You must access the DB Connection via `MongoDB.conn()`.")
