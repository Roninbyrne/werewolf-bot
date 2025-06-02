import logging
from pyrogram import filters
from pyrogram.types import Message
from Werewolf import app
from Werewolf.plugins.base.db import group_log_db, global_userinfo_db

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='error.log',
    filemode='a'
)

async def save_user_info(user):
    if not user:
        return
    userinfo = {
        "_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "is_bot": user.is_bot
    }
    try:
        await global_userinfo_db.update_one({"_id": user.id}, {"$set": userinfo}, upsert=True)
    except Exception as e:
        logging.error(f"Error updating user info for user {user.id}: {e}")

@app.on_message(filters.group & filters.text)
async def auto_save_user_info(client, message: Message):
    await save_user_info(message.from_user)

@app.on_message(filters.command("syncusers") & filters.group)
async def sync_users_command(client, message: Message):
    try:
        await message.reply("🔄 Syncing user data...")

        users = await group_log_db.find({"group_id": message.chat.id}).to_list(length=None)

        updated = 0
        for data in users:
            uid = data.get("user_id")
            if uid:
                try:
                    user = await client.get_users(uid)
                    await save_user_info(user)
                    updated += 1
                except Exception as e:
                    logging.error(f"Failed to fetch or save user {uid}: {e}")

        await message.reply(f"✅ Synced info of {updated} users in this group.")
    except Exception as e:
        logging.error(f"Error in sync_users_command for chat {message.chat.id}: {e}")
        await message.reply("❌ An error occurred while syncing user data. Please try again later.")