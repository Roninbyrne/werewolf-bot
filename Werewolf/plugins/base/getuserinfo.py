from pyrogram import Client, filters
from pyrogram.types import Message
from Werewolf import app
from Werewolf.plugins.base.db import global_userinfo_db

async def is_user_saved(user_id: int) -> bool:
    return await global_userinfo_db.find_one({"_id": user_id}) is not None

async def save_user_info(user):
    if not user or user.is_bot:
        return

    if await is_user_saved(user.id):
        return

    userinfo = {
        "_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "is_bot": user.is_bot,
    }

    await global_userinfo_db.insert_one(userinfo)

def setup_user_tracking(app: Client):
    @app.on_message(filters.all)
    async def track_user_data(client: Client, message: Message):
        await save_user_info(message.from_user)

    @app.on_message(filters.command("fetchusers") & filters.group)
    async def fetch_group_users(client: Client, message: Message):
        chat_id = message.chat.id
        sent_message = await message.reply_text("Fetching all users info from this group...")

        count = 0
        async for member in client.iter_chat_members(chat_id):
            user = member.user
            if user and not user.is_bot:
                if not await is_user_saved(user.id):
                    await save_user_info(user)
                    count += 1

        await sent_message.edit_text(f"Completed fetching users from this group.\nNew users saved: {count}")