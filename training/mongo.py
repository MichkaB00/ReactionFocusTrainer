import os
from functools import lru_cache

from pymongo import MongoClient


@lru_cache(maxsize=1)
def get_collection():
    client = MongoClient(
        os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"),
        serverSelectionTimeoutMS=1500,
        connectTimeoutMS=1500,
        socketTimeoutMS=3000,
        tz_aware=True,
    )
    return client["reaction_trainer"]["training_sessions"]
