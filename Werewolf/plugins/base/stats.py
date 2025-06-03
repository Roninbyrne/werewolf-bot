from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from Werewolf import app
from Werewolf.plugins.base.db import global_userinfo_db, global_ban_db
from Werewolf.core.bottrack import group_log_db
from config import STATS_VIDEO

@app.on_message(filters.command("stats"))
async def show_stats(client: Client, message):
    group_count = await group_log_db.count_documents({})
    user_count = await global_userinfo_db.count_documents({})
    banned_count = await global_ban_db.count_documents({})

    caption = (
        f"📊 <b>Bot Statistics</b>\n\n"
        f"👥 Connected Groups: <b>{group_count}</b>\n"
        f"👤 Connected Users: <b>{user_count}</b>\n"
        f"🚫 Globally Banned: <b>{banned_count}</b>\n\n"
        f'<a href="{STATS_VIDEO}">๏ Here is the stats 🐺</a>'
    )

    await message.reply(
        caption,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Close", callback_data="stats_close")]]
        ),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=False
    )

@app.on_callback_query(filters.regex("stats_close"))
async def close_stats_message(client: Client, callback_query):
    try:
        await callback_query.message.delete()
    except:
        pass