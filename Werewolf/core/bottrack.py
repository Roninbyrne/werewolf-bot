import logging
from Werewolf import app
from pyrogram import filters
from pyrogram.types import Chat, ChatMemberUpdated, Message
from pyrogram.enums import ChatMemberStatus, ChatAction
from pyrogram.errors import PeerIdInvalid
from pyrogram.raw.functions.channels import GetChannels
from pyrogram.raw.types import InputChannel, InputPeerChannel
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB_URI, OWNER_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Werewolf.core.bottrack")

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

        if new_status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            channel_id = int(str(chat.id).replace("-100", ""))
            access_hash = None
            try:
                input_channel = InputChannel(channel_id=channel_id, access_hash=0)
                result = await client.invoke(GetChannels(id=[input_channel]))
                if result.chats:
                    raw_chat = result.chats[0]
                    access_hash = getattr(raw_chat, "access_hash", None)
            except Exception as e:
                logger.warning(f"Failed to fetch access_hash for {chat.id}: {e}")

            old_data = await group_log_db.find_one({"_id": chat.id})
            group_data = {
                "_id": chat.id,
                "title": chat.title,
                "username": chat.username,
                "type": chat.type.value,
                "is_admin": new_status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER),
                "access_hash": int(access_hash) if access_hash else int(old_data.get("access_hash")) if old_data and old_data.get("access_hash") else None,
            }

            logger.info(f"Bot added/promoted in group: {group_data}")
            await group_log_db.update_one({"_id": chat.id}, {"$set": group_data}, upsert=True)

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
        raw_access_hash = group.get("access_hash")
        access_hash = int(raw_access_hash) if raw_access_hash is not None else None
        try:
            if access_hash is not None:
                try:
                    input_peer = InputPeerChannel(
                        channel_id=int(str(chat_id).replace("-100", "")),
                        access_hash=access_hash
                    )
                    chat = await client.get_chat(input_peer)
                    chat_id = chat.id
                    member = await client.get_chat_member(chat_id, me.id)
                except Exception as e:
                    logger.warning(f"Failed to recover group {chat_id} with access_hash: {e}")
                    continue
            else:
                try:
                    await client.send_chat_action(chat_id, ChatAction.TYPING)
                    chat = await client.get_chat(chat_id)
                    member = await client.get_chat_member(chat_id, me.id)
                except PeerIdInvalid:
                    logger.warning(f"Group {chat_id} is missing access_hash, skipping.")
                    continue
        except Exception as e:
            logger.warning(f"Error verifying group {chat_id}: {e}")
            continue

        if member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            group_data = {
                "_id": chat.id,
                "title": chat.title,
                "username": chat.username,
                "type": chat.type.value,
                "is_admin": member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER),
                "access_hash": access_hash,
            }

            logger.info(f"Verifying group from DB: {group_data}")
            await group_log_db.update_one({"_id": chat.id}, {"$set": group_data}, upsert=True)

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