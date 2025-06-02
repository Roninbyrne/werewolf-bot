from pyrogram import filters
from pyrogram.types import Message
from Werewolf import app
from Werewolf.plugins.base.db import group_log_db, global_userinfo_db

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
    await global_userinfo_db.update_one({"_id": user.id}, {"$set": userinfo}, upsert=True)

@app.on_message(filters.group & filters.text)
async def auto_save_user_info(client, message: Message):
    await save_user_info(message.from_user)

@app.on_message(filters.command("syncusers") & filters.group)
async def sync_users_command(client, message: Message):
    if not message.from_user or not message.from_user.id:
        return

    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ("administrator", "creator"):
        await message.reply("You need to be an admin to run this command.")
        return

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
                print(f"Failed to fetch user {uid}: {e}")

    await message.reply(f"✅ Synced info of {updated} users in this group.")