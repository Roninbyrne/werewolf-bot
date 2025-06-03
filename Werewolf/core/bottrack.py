import logging
from werewolf import app
from pyrogram.types import Chat, ChatMemberUpdated
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB_URI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo_client["store"]
group_collection = db["groups"]


@app.on_my_chat_member()
async def handle_bot_status_change(client, update: ChatMemberUpdated):
    chat: Chat = update.chat
    new_status = update.new_chat_member.status

    if new_status in ("member", "administrator", "creator"):
        group_data = {
            "_id": chat.id,
            "title": chat.title,
            "username": chat.username,
            "type": chat.type,
            "is_admin": new_status in ("administrator", "creator"),
        }

        try:
            await group_collection.update_one(
                {"_id": chat.id},
                {"$set": group_data},
                upsert=True
            )
            logger.info(f"✅ Bot added/promoted in group: '{chat.title}' [ID: {chat.id}]. Data stored/updated.")
        except Exception as e:
            logger.error(f"❌ Error saving group data for '{chat.title}' [ID: {chat.id}]: {e}")

    else:
        logger.info(f"ℹ️ Bot status changed to '{new_status}' in '{chat.title}' [ID: {chat.id}] — no action taken.")


if __name__ == "__main__":
    logger.info("🚀 Bot is starting...")
    app.run()