from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.enums import ParseMode

import config
from Werewolf import app
from Werewolf.plugins.base.logging_toggle import is_logging_enabled
from Werewolf.core.mongo import global_userinfo_db, players_col
from config import LOGGER_ID
from bson import ObjectId


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

    if message.text.startswith("/start reveal_"):
        try:
            game_id = ObjectId(message.text.split("_")[1])
            player = await players_col.find_one({"_id": user.id, "game_id": game_id})
            if not player:
                await message.reply("❌ You are not part of this game.")
                return
            role = player.get("role", "Unknown").capitalize()
            disguised = player.get("disguised", False)
            text = f"🎭 Role: *{role}*"
            if disguised:
                text += "\n🕵️‍♂️ You are currently disguised."
            await message.reply(text, parse_mode=ParseMode.MARKDOWN)
            return
        except:
            await message.reply("❌ Invalid game ID.")
            return

    if message.text.startswith("/start vote_"):
        try:
            game_id = ObjectId(message.text.split("_")[1])
            player = await players_col.find_one({"_id": user.id, "game_id": game_id})
            if not player or player.get("role") not in ["werewolf", "alpha"]:
                await message.reply("❌ You are not eligible to vote.")
                return

            players = await players_col.find({
                "game_id": game_id,
                "_id": {"$ne": user.id}
            }).to_list(length=100)

            buttons = [
                [InlineKeyboardButton((await client.get_users(p["_id"])).first_name, callback_data=f"target_wvote_{p['_id']}")]
                for p in players
            ]

            await message.reply("🩸 Choose your prey for tonight:", reply_markup=InlineKeyboardMarkup(buttons))
            return
        except:
            await message.reply("❌ Something went wrong.")
            return

    if message.text.startswith("/start heal_"):
        try:
            game_id = ObjectId(message.text.split("_")[1])
            player = await players_col.find_one({"_id": user.id, "game_id": game_id})
            if not player or player.get("role") != "doctor":
                await message.reply("❌ You are not allowed to heal.")
                return

            players = await players_col.find({
                "game_id": game_id,
                "_id": {"$ne": user.id}
            }).to_list(length=100)

            buttons = [
                [InlineKeyboardButton((await client.get_users(p["_id"])).first_name, callback_data=f"target_heal_{p['_id']}")]
                for p in players
            ]

            await message.reply("🩺 Choose someone to heal tonight:", reply_markup=InlineKeyboardMarkup(buttons))
            return
        except:
            await message.reply("❌ Something went wrong.")
            return

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
