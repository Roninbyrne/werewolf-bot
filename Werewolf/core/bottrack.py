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
group_members_db = db["group_members"]

@app.on_chat_member_updated()
async def handle_bot_status_change(client, update: ChatMemberUpdated):
    try:
        if not update.new_chat_member or not update.new_chat_member.user:
            logger.debug("Skipped update with no new_chat_member or user info.")
            return

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
                "type": chat.type.value,
                "is_admin": new_status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER),
            }

            await group_log_db.update_one(
                {"_id": chat.id},
                {"$set": group_data},
                upsert=True
            )
            logger.info(f"✅ Group data stored/updated for: '{chat.title}' [ID: {chat.id}]")

            logger.info(f"📥 Fetching visible members for group: '{chat.title}' [ID: {chat.id}] (admin: {group_data['is_admin']})")
            visible_count = 0
            async for member in client.get_chat_members(chat.id):
                try:
                    user = member.user
                    member_data = {
                        "group_id": chat.id,
                        "user_id": user.id,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "username": user.username,
                        "status": member.status.value,
                    }
                    await group_members_db.update_one(
                        {"group_id": chat.id, "user_id": user.id},
                        {"$set": member_data},
                        upsert=True
                    )
                    visible_count += 1
                except Exception as user_err:
                    logger.warning(f"⚠️ Failed to store user {member.user.id} in group '{chat.title}': {user_err}")
            logger.info(f"✅ Stored {visible_count} visible members for group: '{chat.title}' [ID: {chat.id}]")

        else:
            logger.info(f"ℹ️ Bot status '{new_status}' in group '{chat.title}' [ID: {chat.id}] — ignored.")

    except Exception as e:
        logger.exception(f"❌ Unexpected error in status change handler: {e}")

if __name__ == "__main__":
    logger.info("🚀 Bot is starting...")
    app.run()