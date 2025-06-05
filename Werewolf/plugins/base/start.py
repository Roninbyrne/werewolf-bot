from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

import config
from Werewolf import app
from Werewolf.plugins.base.logging_toggle import is_logging_enabled
from Werewolf.core.mongo import global_userinfo_db
from config import LOGGER_ID


@app.on_message(filters.command("start") & filters.private)
async def start_pm(client, message: Message):
    user = message.from_user

    userinfo = {
        "_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "is_bot": user.is_bot
    }
    await global_userinfo_db.update_one({"_id": user.id}, {"$set": userinfo}, upsert=True)

    if await is_logging_enabled():
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = f"@{user.username}" if user.username else "N/A"
        log_text = (
            f"📩 <b>User Started the Bot</b>\n\n"
            f"👤 <b>Name:</b> {full_name}\n"
            f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
            f"🔗 <b>Username:</b> {username}"
        )
        await client.send_message(LOGGER_ID, log_text)

    text = (
        f"<b>нєу {user.first_name}.\n"
        f"๏ ɪᴍ 𝗪ᴇʀᴇᴡᴏʟꜰ 花 子 — ᴀ ᴍᴜʟᴛɪ-ᴘʟᴀʏᴇʀ ɢᴀᴍᴇ ʙᴏᴛ ʙᴀꜱᴇᴅ ᴏɴ ᴛʜᴇ ᴄʟᴀꜱꜱɪᴄ ᴡᴇʀᴇᴡᴏʟꜰ ɢᴀᴍᴇ.\n"
        f"๏ ᴛᴀᴘ ᴛʜᴇ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ ᴛᴏ ɢᴇᴛ ꜱᴛᴀʀᴛᴇᴅ ᴏʀ ꜱᴇᴇ ᴄᴏᴍᴍᴀɴᴅꜱ.</b>"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Me To Group ➕", url=f"https://t.me/{app.me.username}?startgroup=true")],
        [
            InlineKeyboardButton("Support Chat", url=config.SUPPORT_CHAT),
            InlineKeyboardButton("Support Channel", url=config.SUPPORT_CHANNEL)
        ],
        [InlineKeyboardButton("📚 Help and Commands", callback_data="help_menu")]
    ])

    await message.reply(
        f"{text}\n\n<a href='{config.START_VIDEO}'>๏ ʟᴇᴛ'ꜱ ʙᴇɢɪɴ ᴛʜᴇ ʜᴜɴᴛ! 🐺</a>",
        reply_markup=keyboard
    )


@app.on_callback_query(filters.regex("help_menu"))
async def help_menu(client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣", callback_data="help_1"), InlineKeyboardButton("2️⃣", callback_data="help_2")],
        [InlineKeyboardButton("3️⃣", callback_data="help_3"), InlineKeyboardButton("4️⃣", callback_data="help_4")],
        [InlineKeyboardButton("❌ Close", callback_data="close")]
    ])
    await callback_query.message.edit_text(
        f"<a href='{config.HELP_MENU_VIDEO}'>๏ Watch the Help Menu Video 🐺</a>\n\n📖 Choose a help topic below:",
        reply_markup=keyboard
    )


@app.on_callback_query(filters.regex(r"help_[1-4]"))
async def show_help_section(client, callback_query: CallbackQuery):
    section = callback_query.data[-1]

    help_texts = {
        "1": "📘 <b>Help Topic 1</b>\n\nYou can add full description here.",
        "2": "📙 <b>Help Topic 2</b>\n\nThis could be about how to join and start a game.",
        "3": "📗 <b>Help Topic 3</b>\n\nExplain game roles or admin commands here.",
        "4": "📕 <b>Help Topic 4</b>\n\nAdd advanced gameplay or dev info here."
    }

    help_videos = {
        "1": config.HELP_VIDEO_1,
        "2": config.HELP_VIDEO_2,
        "3": config.HELP_VIDEO_3,
        "4": config.HELP_VIDEO_4
    }

    await callback_query.message.edit_text(
        f"<a href='{help_videos[section]}'>๏ Watch Help Video 🎬</a>\n\n{help_texts[section]}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="help_menu")]
        ])
    )


@app.on_callback_query(filters.regex("close"))
async def close_menu(client, callback_query: CallbackQuery):
    await callback_query.message.delete()