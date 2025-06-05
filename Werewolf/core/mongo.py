from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB_URI
from ..logging import LOGGER

LOGGER(__name__).info("Connecting to your Mongo Database...")
try:
    mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
    db = mongo_client["store"]

    group_log_db = db["group_logs"]
    group_members_db = db["group_members"]
    global_ban_db = db["global_bans"]
    global_userinfo_db = db["user_info"]

    LOGGER(__name__).info("Connected to your Mongo Database.")
except Exception as e:
    LOGGER(__name__).error(f"Failed to connect to your Mongo Database: {e}")
    exit()