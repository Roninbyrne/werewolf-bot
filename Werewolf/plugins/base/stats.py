from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Werewolf import app
from Werewolf.plugins.base.db import group_log_db, global_userinfo_db, global_ban_db
from config import STATS_VIDEO

@app.on_message(filters.command("stats"))
async def show_stats(client: Client, message):
    group_count = group_log_db.count_documents({})
    user_count = global_userinfo_db.count_documents({})
    banned_count = global_ban_db.count_documents({})

    caption = (
        f"📊 <b>Bot Statistics</b>\n\n"
        f"👥 Connected Groups: <b>{group_count}</b>\n"
        f"👤 Connected Users: <b>{user_count}</b>\n"
        f"🚫 Globally Banned: <b>{banned_count}</b>\n\n"
        f"Here is the stats."
    )

    await message.reply_video(
        video=START_VIDEO,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Close", callback_data="stats_close")]]
        )
    )

@app.on_callback_query(filters.regex("stats_close"))
async def close_stats_message(client: Client, callback_query):
    try:
        await callback_query.message.delete()
    except:
        pass