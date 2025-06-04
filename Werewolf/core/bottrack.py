import logging
from Werewolf import app
from pyrogram.types import Chat, ChatMemberUpdated, Message
from pyrogram.enums import ChatMemberStatus
from pyrogram import filters
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB_URI, OWNER_ID

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
            return

        bot_id = (await client.get_me()).id
        if update.new_chat_member.user.id != bot_id:
            return

        chat: Chat = update.chat
        new_status = update.new_chat_member.status

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
                except Exception:
                    continue
    except Exception as e:
        logger.exception(f"❌ Unexpected error in status change handler: {e}")

@app.on_message(filters.command("verifygroups") & filters.user(OWNER_ID))
async def verify_groups_command(client, message: Message):
    try:
        me = await client.get_me()
        updated_groups = []

        async for dialog in client.get_dialogs():
            chat = dialog.chat
            if chat.type in ("group", "supergroup"):
                try:
                    member = await client.get_chat_member(chat.id, me.id)
                    if member.status in (
                        ChatMemberStatus.MEMBER,
                        ChatMemberStatus.ADMINISTRATOR,
                        ChatMemberStatus.OWNER,
                    ):
                        group_data = {
                            "_id": chat.id,
                            "title": chat.title,
                            "username": chat.username,
                            "type": chat.type.value,
                            "is_admin": member.status in (
                                ChatMemberStatus.ADMINISTRATOR,
                                ChatMemberStatus.OWNER,
                            ),
                        }
                        await group_log_db.update_one(
                            {"_id": chat.id},
                            {"$set": group_data},
                            upsert=True
                        )
                        updated_groups.append(f"{chat.title} [`{chat.id}`]")
                except Exception:
                    continue

        if updated_groups:
            group_list_text = "\n".join(updated_groups)
            reply_text = f"✅ Verified and updated {len(updated_groups)} groups:\n\n{group_list_text}"
        else:
            reply_text = "ℹ️ No groups found or updated."

        await message.reply_text(reply_text)
    except Exception as e:
        await message.reply_text(f"❌ Error verifying groups: {e}")

if __name__ == "__main__":
    logger.info("🚀 Bot is starting...")
    app.run()