from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB_URI

mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo_client["storage"]

group_log_db = db["group_logs"]
global_ban_db = db["global_bans"]
global_userinfo_db = db["user_info"]