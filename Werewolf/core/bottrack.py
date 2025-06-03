import logging
from Werewolf import app
from pyrogram.types import Chat, ChatMemberUpdated
from pyrogram.enums import ChatMemberStatus
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB_URI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo_client["store"]
group_log_db = db["group_logs"]


@app.on_chat_member_updated()
async def handle_bot_status_change(client, update: ChatMemberUpdated):
    try:
        bot_id = (await client.get_me()).id
        if update.new_chat_member.user.id != bot_id:
            logger.debug(f"Ignored update not related to the bot (User ID: {update.new_chat_member.user.id})")
            return

        chat: Chat = update.chat
        new_status = update.new_chat_member.status

        logger.info(f"Detected status change in group '{chat.title}' [ID: {chat.id}] to '{new_status}'")

        if new_status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        ):
            group_data = {
                "_id": chat.id,
                "title": chat.title,
                "username": chat.username,
                "type": chat.type,
                "is_admin": new_status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER),
            }

            await group_log_db.update_one(
                {"_id": chat.id},
                {"$set": group_data},
                upsert=True
            )
            logger.info(f"✅ Group data stored/updated for: '{chat.title}' [ID: {chat.id}]")
        else:
            logger.info(f"ℹ️ Bot status '{new_status}' in group '{chat.title}' [ID: {chat.id}] — ignored.")

    except Exception as e:
        logger.exception(f"❌ Unexpected error in status change handler: {e}")


if __name__ == "__main__":
    logger.info("🚀 Bot is starting...")
    app.run()