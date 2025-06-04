import logging
from Werewolf import app
from pyrogram.types import Chat, ChatMemberUpdated, Message
from pyrogram.enums import ChatMemberStatus, ChatAction
from pyrogram import filters
from pyrogram.errors import PeerIdInvalid
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
                "access_hash": getattr(chat, "access_hash", None),
            }

            await group_log_db.update_one(
                {"_id": chat.id},
                {"$set": group_data},
                upsert=True
            )
            logger.info(f"Stored group: {chat.title} [{chat.id}]")

            count = 0
            async for member in client.get_chat_members(chat.id):
                try:
                    user = member.user
                    member_data = {
                        "group_id": chat.id,
                        "user_id": user.id,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "username": user.username,
                        "status": getattr(member.status, "value", member.status),
                    }
                    await group_members_db.update_one(
                        {"group_id": chat.id, "user_id": user.id},
                        {"$set": member_data},
                        upsert=True
                    )
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to store user in group {chat.id}: {e}")
            logger.info(f"Stored {count} members for group: {chat.title} [{chat.id}]")
    except Exception as e:
        logger.exception(f"Error in bot status change handler: {e}")

async def verify_all_groups_from_db(client):
    me = await client.get_me()
    updated_groups = []

    async for group in group_log_db.find({}):
        chat_id = group["_id"]
        try:
            await client.send_chat_action(chat_id, ChatAction.TYPING)
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
                    "access_hash": getattr(chat, "access_hash", None),
                }
                await group_log_db.update_one(
                    {"_id": chat.id},
                    {"$set": group_data},
                    upsert=True
                )

                count = 0
                async for member in client.get_chat_members(chat.id):
                    try:
                        user = member.user
                        member_data = {
                            "group_id": chat.id,
                            "user_id": user.id,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "username": user.username,
                            "status": getattr(member.status, "value", member.status),
                        }
                        await group_members_db.update_one(
                            {"group_id": chat.id, "user_id": user.id},
                            {"$set": member_data},
                            upsert=True
                        )
                        count += 1
                    except Exception as e:
                        logger.warning(f"Failed to store user in group {chat.id}: {e}")
                logger.info(f"Verified {chat.title} [{chat.id}] with {count} members")
                updated_groups.append(f"{chat.title} [`{chat.id}`]")
            else:
                logger.info(f"Bot not present in group {chat_id}, skipping.")
        except PeerIdInvalid:
            logger.warning(f"PeerIdInvalid for group {chat_id}, skipping.")
            continue
        except Exception as e:
            logger.warning(f"Error verifying group {chat_id}: {e}")
            continue

    return updated_groups

@app.on_message(filters.command("verifygroups") & filters.user(OWNER_ID))
async def verify_groups_command(client, message: Message):
    try:
        logger.info(f"Manual verify triggered by {message.from_user.id}")
        updated_groups = await verify_all_groups_from_db(client)

        if updated_groups:
            reply_text = f"Verified {len(updated_groups)} groups:\n\n" + "\n".join(updated_groups)
        else:
            reply_text = "No valid groups found or bot not a member."

        await message.reply_text(reply_text)
        logger.info("Manual group verification completed.")
    except Exception as e:
        logger.exception("Error during manual verify.")
        await message.reply_text(f"Error verifying groups: {e}")
