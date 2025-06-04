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
            logger.info(f"✅ Group data stored/updated for: '{chat.title}' [ID: {chat.id}']")

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
            logger.info(f"✅ Stored {visible_count} visible members for group: '{chat.title}' [ID: {chat.id}']")

        else:
            logger.info(f"ℹ️ Bot status '{new_status}' in group '{chat.title}' [ID: {chat.id}] — ignored.")

    except Exception as e:
        logger.exception(f"❌ Unexpected error in status change handler: {e}")


async def verify_all_groups_from_db(client):
    me = await client.get_me()
    updated_groups = []

    async for group in group_log_db.find({}):
        chat_id = group["_id"]
        try:
            chat = await client.get_chat(chat_id)
            member = await client.get_chat_member(chat_id, me.id)

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
                logger.info(f"✅ Verified group: '{chat.title}' [ID: {chat.id}']")
            else:
                logger.info(f"❌ Bot is no longer a member/admin in group ID: {chat_id}")

        except Exception as e:
            logger.warning(f"⚠️ Skipped group ID {chat_id} due to error: {e}")
            continue

    return updated_groups


@app.on_message(filters.command("verifygroups") & filters.user(OWNER_ID))
async def verify_groups_command(client, message: Message):
    try:
        logger.info(f"🔍 Starting group verification triggered by {message.from_user.id}")
        updated_groups = await verify_all_groups_from_db(client)

        if updated_groups:
            group_list_text = "\n".join(updated_groups)
            reply_text = f"✅ Verified and updated {len(updated_groups)} groups:\n\n{group_list_text}"
        else:
            reply_text = "ℹ️ No valid groups found in MongoDB or bot is no longer a member."

        await message.reply_text(reply_text)
        logger.info("✅ Group verification completed successfully.")
    except Exception as e:
        logger.exception("❌ Error during /verifygroups execution.")
        await message.reply_text(f"❌ Error verifying groups: {e}")

if __name__ == "__main__":
    logger.info("🚀 Bot is starting...")
    app.run()
