import logging
from Werewolf import app
from pyrogram import filters
from pyrogram.types import Chat, ChatMemberUpdated, Message
from pyrogram.enums import ChatMemberStatus, ChatAction
from pyrogram.errors import PeerIdInvalid
from pyrogram.raw.functions.channels import GetChannels
from pyrogram.raw.types import InputChannel
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB_URI, OWNER_ID, LOGGER_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Werewolf.core.bottrack")

mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo_client["store"]
group_log_db = db["group_logs"]
group_members_db = db["group_members"]

@app.on_chat_member_updated()
async def handle_bot_status_change(client, update: ChatMemberUpdated):
    try:
        bot_id = (await client.get_me()).id

        old_user = update.old_chat_member.user if update.old_chat_member else None
        new_user = update.new_chat_member.user if update.new_chat_member else None

        if (old_user and old_user.id == bot_id) or (new_user and new_user.id == bot_id):
            chat: Chat = update.chat
            new_status = update.new_chat_member.status if update.new_chat_member else None

            if new_status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED) or not update.new_chat_member:
                await group_log_db.delete_one({"_id": chat.id})
                await group_members_db.delete_many({"group_id": chat.id})
                await client.send_message(
                    LOGGER_ID,
                    f"❌ Bot removed from group: {chat.title} [`{chat.id}`]"
                )
                logger.info(f"❌ Bot was removed from group {chat.id} — deleted from DB.")
                logger.info(f"[DUB] Removed group {chat.title} [{chat.id}] from DB.")
                return

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

                await client.send_message(
                    LOGGER_ID,
                    f"✅ Bot added to group: {chat.title} [`{chat.id}`]\n👤 Members saved: {count}"
                )
                logger.info(f"Bot added to group: {group_data}")
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

        chat = None
        member = None
        used_fallback = False

        if access_hash:
            try:
                channel_id = int(str(chat_id).replace("-100", ""))
                input_channel = InputChannel(channel_id=channel_id, access_hash=access_hash)
                result = await client.invoke(GetChannels(id=[input_channel]))
                if result.chats:
                    raw_chat = result.chats[0]
                    chat = await client.get_chat(raw_chat.id)
                    chat_id = chat.id
                    member = await client.get_chat_member(chat_id, me.id)
            except Exception:
                used_fallback = True

        if not chat:
            try:
                await client.send_chat_action(chat_id, ChatAction.TYPING)
                chat = await client.get_chat(chat_id)
                member = await client.get_chat_member(chat_id, me.id)
            except PeerIdInvalid:
                if used_fallback or access_hash:
                    logger.warning(f"❌ Failed to recover group {chat_id} — both access_hash and fallback failed.")
                continue
            except Exception:
                continue

        if used_fallback:
            logger.info(f"🔁 Recovered group {chat_id} via fallback (access_hash invalid or expired).")

        if member and member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            group_data = {
                "_id": chat.id,
                "title": chat.title,
                "username": chat.username,
                "type": chat.type.value,
                "is_admin": member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER),
                "access_hash": access_hash,
            }

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

            logger.info(f"✅ Verified {chat.title} [{chat.id}] with {count} members")
            updated_groups.append(f"{chat.title} [`{chat.id}`]")

    return updated_groups

async def get_all_groups_summary():
    try:
        group_count = await group_log_db.count_documents({})
        groups = group_log_db.find({})
        group_summaries = []

        async for group in groups:
            name = group.get("title", "Unknown Title")
            chat_id = group.get("_id")
            member_count = await group_members_db.count_documents({"group_id": chat_id})
            summary = f"{name} [`{chat_id}`] - 👤 {member_count} members"
            group_summaries.append(summary)
            logger.info(f"[DUB] {summary}")

        logger.info(f"Total Groups: {group_count}")
        return group_count, group_summaries
    except Exception as e:
        logger.exception("Failed to fetch groups summary from DB")
        return 0, []

@app.on_message(filters.command("groupstats") & filters.user(OWNER_ID))
async def send_group_stats(client, message: Message):
    count, summaries = await get_all_groups_summary()
    text = f"**Total Groups:** {count}\n\n" + "\n".join(summaries)
    await message.reply_text(text or "No groups found.")

async def verify_groups_command(client, message: Message):
    updated_groups = await verify_all_groups_from_db(client)
    text = "✅ Verified Groups:\n\n" + "\n".join(updated_groups) if updated_groups else "No groups verified."
    if message:
        await message.reply_text(text)
