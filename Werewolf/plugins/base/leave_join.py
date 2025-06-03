from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatMemberUpdated
from Werewolf.plugins.base.db import group_log_db
from config import LOGGER_ID
from Werewolf import app
from Werewolf.plugins.base.logging_toggle import is_logging_enabled


@app.on_chat_member_updated()
async def log_group_events(client: Client, chat_member: ChatMemberUpdated):
    bot_id = (await client.get_me()).id
    new_member = chat_member.new_chat_member
    old_member = chat_member.old_chat_member

    if not new_member or new_member.user.id != bot_id:
        return

    chat = chat_member.chat
    group_id = chat.id

    if (
        old_member is None or old_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]
    ) and new_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]:
        try:
            invite_link = await client.export_chat_invite_link(group_id)
        except:
            invite_link = "Not available"

        try:
            member_count = (await client.get_chat(group_id)).members_count
        except:
            member_count = "Unknown"

        group_info = {
            "_id": group_id,
            "title": chat.title,
            "username": chat.username,
            "link": invite_link,
            "members": member_count
        }

        await group_log_db.update_one({"_id": group_id}, {"$set": group_info}, upsert=True)

        if await is_logging_enabled():
            text = (
                f"✅ <b>Bot added to group</b>\n\n"
                f"📌 <b>Group Name:</b> {chat.title}\n"
                f"🆔 <b>Group ID:</b> <code>{group_id}</code>\n"
                f"🔗 <b>Group Link:</b> {invite_link}\n"
                f"👤 <b>Username:</b> @{chat.username or 'None'}\n"
                f"👥 <b>Members:</b> {member_count}"
            )
            await client.send_message(LOGGER_ID, text)