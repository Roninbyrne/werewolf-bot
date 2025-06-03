from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatMemberUpdated, ChatMemberUpdatedHandler

from Werewolf import app
from Werewolf.plugins.base.db import group_log_db


async def handle_bot_updates(client: Client, event: ChatMemberUpdated):
    chat_id = event.chat.id
    chat_title = event.chat.title or "Private Chat"

    if event.new_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]:
        await group_log_db.update_one(
            {"chat_id": chat_id},
            {"$set": {
                "chat_id": chat_id,
                "chat_title": chat_title,
                "status": "active"
            }},
            upsert=True
        )

    elif event.new_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
        await group_log_db.update_one(
            {"chat_id": chat_id},
            {"$set": {"status": "removed"}}
        )


app.add_handler(ChatMemberUpdatedHandler(handle_bot_updates))