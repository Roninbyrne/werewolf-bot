import os
import asyncio
import logging
from datetime import datetime
import pytz
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Werewolf import app
from config import OWNER_ID, LOGGER_ID
from Werewolf.plugins.base.logging_toggle import is_logging_enabled

@app.on_message(filters.command("restart"))
async def restart_command_handler(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply_text("🚫 You are not Owner to raise this cmd.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Restart", callback_data="confirm_restart"),
         InlineKeyboardButton("❌ Cancel", callback_data="cancel_restart")]
    ])
    await message.reply_text("⚠️ R U Sure to Reboot Bot?", reply_markup=keyboard)

@app.on_callback_query(filters.user(OWNER_ID) & filters.regex("confirm_restart"))
async def confirm_restart_handler(client: Client, callback_query: CallbackQuery):
    await callback_query.message.delete()
    msg = await callback_query.message.reply_text("🔄 Restarting bot... Please wait.")

    if await is_logging_enabled():
        ist = pytz.timezone("Asia/Kolkata")
        time_now = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
        await client.send_message(
            LOGGER_ID,
            f"♻️ <b>Bot is restarting...</b>\n⏰ <b>Time:</b> <code>{time_now} IST</code>\n🔍 Will reverify MongoDB group data on boot."
        )

    os.system(f"kill -9 {os.getpid()} && bash start")

@app.on_callback_query(filters.user(OWNER_ID) & filters.regex("cancel_restart"))
async def cancel_restart_handler(client: Client, callback_query: CallbackQuery):
    await callback_query.message.delete()
    msg = await callback_query.message.reply_text("❌ Restart request revoked.")
    await asyncio.sleep(4)
    await msg.delete()