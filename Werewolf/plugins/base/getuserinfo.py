from pyrogram import Client, filters
from pyrogram.types import Message
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