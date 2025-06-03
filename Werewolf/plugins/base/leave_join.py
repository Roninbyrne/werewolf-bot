lfrom pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatMemberUpdated
from Werewolf.plugins.base.db import group_log_db
from config import LOGGER_ID
import asyncio

from Werewolf import app
from Werewolf.plugins.base.logging_toggle import is_logging_enabled

bot_id = None


@app.on_chat_member_updated()
async def log_group_events(client: Client, chat_member: ChatMemberUpdated):
    global bot_id
    if bot_id is None:
        bot_id = (await client.get_me()).id

    if chat_member.new_chat_member.user.id != bot_id:
        return

    if chat_member.old_chat_member and chat_member.old_chat_member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
        return

    if chat_member.new_chat_member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]:
        return

    chat = chat_member.chat
    group_id = chat.id

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
        "title": chat.title or "Unknown",
        "username": chat.username,
        "link": invite_link,
        "members": member_count
    }

    await group_log_db.update_one({"_id": group_id}, {"$set": group_info}, upsert=True)

    if await is_logging_enabled():
        text = (
            f"✅ <b>Bot added to group</b>\n\n"
            f"📌 <b>Group Name:</b> {chat.title or 'Unknown'}\n"
            f"🆔 <b>Group ID:</b> <code>{group_id}</code>\n"
            f"🔗 <b>Group Link:</b> {invite_link}\n"
            f"👤 <b>Username:</b> @{chat.username or 'None'}\n"
            f"👥 <b>Members:</b> {member_count}"
        )
        await client.send_message(LOGGER_ID, text)


async def check_bot_removal():
    await asyncio.sleep(60)  # Delay after start
    global bot_id
    if bot_id is None:
        bot_id = (await app.get_me()).id

    while True:
        async for group in group_log_db.find():
            group_id = group["_id"]
            try:
                member = await app.get_chat_member(group_id, bot_id)
                if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
                    raise Exception("Bot removed")
            except Exception:
                await group_log_db.delete_one({"_id": group_id})
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
        await asyncio.sleep(300)


def start_removal_monitor():
    asyncio.create_task(check_bot_removal())