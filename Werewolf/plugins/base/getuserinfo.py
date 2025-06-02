import asyncio
import random
from Werewolf import app
from Werewolf.plugins.base.db import group_log_db, global_userinfo_db
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import PeerIdInvalid

async def background_sync_loop():
    while True:
        group_ids = await group_log_db.distinct("group_name")  # group_name stores group_id as string

        for group_id in group_ids:
            group_data = await group_log_db.find({"group_name": group_id}).to_list(None)
            if not group_data:
                continue

            for data in group_data:
                user_id = data.get("user_id")
                if not user_id:
                    continue

                try:
                    user = await app.get_users(user_id)
                    userinfo = {
                        "_id": user.id,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "username": user.username,
                        "is_bot": user.is_bot
                    }
                    await global_userinfo_db.update_one({"_id": user.id}, {"$set": userinfo}, upsert=True)
                except PeerIdInvalid:
                    continue

                await asyncio.sleep(random.uniform(0.5, 1.5))

            await asyncio.sleep(random.randint(2, 6))

        await asyncio.sleep(3600)

@app.on_message(filters.command("sync"))
async def sync_command(client, message):
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="sync_yes"),
            InlineKeyboardButton("No", callback_data="sync_no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(
        "Do you want to manually sync this group's user info to the global database?",
        reply_markup=reply_markup
    )

@app.on_callback_query(filters.regex("sync_"))
async def sync_callback(client, callback_query: CallbackQuery):
    if not callback_query.message.chat:
        return

    group_id = str(callback_query.message.chat.id)
    await callback_query.message.delete()

    if callback_query.data == "sync_yes":
        group_data = await group_log_db.find({"group_name": group_id}).to_list(None)
        success = 0

        for data in group_data:
            user_id = data.get("user_id")
            if not user_id:
                continue

            try:
                user = await app.get_users(user_id)
                userinfo = {
                    "_id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                    "is_bot": user.is_bot
                }
                await global_userinfo_db.update_one({"_id": user.id}, {"$set": userinfo}, upsert=True)
                success += 1
            except PeerIdInvalid:
                continue

        await callback_query.answer(
            f"Manual sync completed for group ID {group_id}.\nTotal synced users: {success}",
            show_alert=True
        )

    elif callback_query.data == "sync_no":
        await callback_query.answer("Sync canceled.", show_alert=True)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(background_sync_loop())
    app.run()