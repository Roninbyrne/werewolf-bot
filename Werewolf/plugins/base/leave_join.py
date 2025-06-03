from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from Werewolf import app
from pyrogram.types import ChatMemberUpdated
from Werewolf.plugins.base.db import group_log_db

@app.on_chat_member_updated()
async def handle_bot_updates(_, event: ChatMemberUpdated):
    if event.new_chat_member.user.is_self:
        chat_id = event.chat.id
        chat_title = event.chat.title or "Private Chat"

        if event.new_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]:
            await group_log_db.update_one(
                {"chat_id": chat_id},
                {"$set": {"chat_id": chat_id, "chat_title": chat_title, "status": "active"}},
                upsert=True
            )
            print(f"Bot added to: {chat_title} [{chat_id}]")

        elif event.new_chat_member.status in [ChatMemberStatus.BANNED, ChatMemberStatus.LEFT]:
            await group_log_db.update_one(
                {"chat_id": chat_id},
                {"$set": {"status": "removed"}}
            )
            print(f"Bot removed from: {chat_title} [{chat_id}]")

if __name__ == "__main__":
    app.run()