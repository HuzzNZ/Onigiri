import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


class OnigiriDB:
    def __init__(self):
        self.client = MongoClient(
            f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASS')}"
            f"@onigiri.cal6d.mongodb.net/?retryWrites=true&w=majority")
        self.db = self.client["Onigiri-Fillings"]
        self.sp = self.db["Special"]

    def set_auto_role_status(self, guild_id: int, status: bool) -> None:
        g = self.sp.find_one({'guild_id': guild_id})
        if g:
            self.sp.update_one(
                {'guild_id': guild_id},
                {'$set': {'auto_role': status}}
            )
        else:
            self.sp.insert_one(
                {
                    'guild_id': guild_id,
                    'purpose': 'auto_role',
                    'auto_role': status
                }
            )

    def get_auto_role_status(self, guild_id: int) -> bool:
        g = self.sp.find_one({'guild_id': guild_id, 'purpose': "auto_role"})
        return False if not g else g.get("auto_role")
