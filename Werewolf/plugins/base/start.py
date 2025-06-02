from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

import config
from Werewolf import app


@app.on_message(filters.command("start") & filters.private)
async def start_pm(client, message: Message):
    text = (
        f"<b>нєу {message.from_user.first_name}.\n"
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
        f"📖 Choose a help topic below:\n\n<a href='{config.HELP_MENU_VIDEO}'>๏ Watch the Help Menu Video 🐺</a>",
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
        f"{help_texts[section]}\n\n<a href='{help_videos[section]}'>๏ Watch Help Video 🎬</a>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="help_menu")]
        ])
    )


@app.on_callback_query(filters.regex("close"))
async def close_menu(client, callback_query: CallbackQuery):
    await callback_query.message.delete()