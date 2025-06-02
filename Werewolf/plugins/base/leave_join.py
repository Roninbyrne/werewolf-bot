from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatMemberUpdated
from pymongo import MongoClient
from config import MONGO_DB_URI, LOGGER_ID
import asyncio

from Werewolf import app
from Werewolf.core.mongo import mongodb
from Werewolf.plugins.base.logging_toggle import is_logging_enabled

mongo_client = MongoClient(MONGO_DB_URI)
group_log_db = mongo_client["Logs"]["group_logs"]


@app.on_chat_member_updated()
async def log_group_events(client: Client, chat_member: ChatMemberUpdated):
    bot_id = (await client.get_me()).id
    new_member = chat_member.new_chat_member
    old_member = chat_member.old_chat_member

    if not (new_member and new_member.user and new_member.user.id == bot_id):
        return

    chat = chat_member.chat
    group_id = chat.id

    if (
        old_member is None or old_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]
    ) and new_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]:
        try:
            invite_link = await client.export_chat_invite_link(group_id)
        except Exception:
            invite_link = "Not available"

        try:
            member_count = (await client.get_chat(group_id)).members_count
        except Exception:
            member_count = "Unknown"

        group_info = {
            "_id": group_id,
            "title": chat.title,
            "username": chat.username,
            "link": invite_link,
            "members": member_count
        }

        group_log_db.update_one({"_id": group_id}, {"$set": group_info}, upsert=True)

        if await is_logging_enabled():
            text = (
                f"✅ <b>Bot added to group</b>\n\n"
                f"📌 <b>Group Name:</b> {chat.title}\n"
                f"🆔 <b>Group ID:</b> <code>{group_id}</code>\n"
                f"🔗 <b>Group Link:</b> {invite_link}\n"
                f"👤 <b>Username:</b> @{chat.username if chat.username else 'None'}\n"
                f"👥 <b>Members:</b> {member_count}"
            )
            await client.send_message(LOGGER_ID, text)


async def check_bot_removal():
    bot = await app.get_me()
    while True:
        groups = group_log_db.find()
        for group in groups:
            group_id = group["_id"]
            try:
                member = await app.get_chat_member(group_id, bot.id)
                if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
                    raise Exception()
            except Exception:
                group_log_db.delete_one({"_id": group_id})
                if await is_logging_enabled():
                    text = (
                        f"❌ <b>Bot removed from group</b>\n\n"
                        f"📌 <b>Group Name:</b> {group.get('title', 'Unknown')}\n"
                        f"🆔 <b>Group ID:</b> <code>{group_id}</code>\n"
                        f"👤 <b>Username:</b> @{group.get('username') or 'None'}"
                    )
                    try:
                        await app.send_message(LOGGER_ID, text)
                    except:
                        pass
            await asyncio.sleep(1)
        await asyncio.sleep(10)


@app.on_startup()
async def startup_tasks(client: Client):
    asyncio.create_task(check_bot_removal())


app.run()