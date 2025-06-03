import logging
from Werewolf import app
from pyrogram.types import Chat, ChatMemberUpdated
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB_URI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo_client["store"]
group_log_db = db["group_logs"]


@app.on_chat_member_updated()
async def handle_bot_status_change(client, update: ChatMemberUpdated):
    if update.new_chat_member.user.id != (await client.get_me()).id:
        return  # Ignore updates not about the bot itself

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
            await group_log_db.update_one(
                {"_id": chat.id},
                {"$set": group_data},
                upsert=True
            )
            logger.info(f"Group: '{chat.title}' [ID: {chat.id}] stored/updated.")
        except Exception as e:
            logger.error(f"DB error for group '{chat.title}' [ID: {chat.id}]: {e}")
    else:
        logger.info(f"Status '{new_status}' in group '{chat.title}' [ID: {chat.id}] — ignored.")


if __name__ == "__main__":
    app.run()