import asyncio
import time
from pyrogram import filters
from pyrogram.types import Message
from Werewolf import app
from Werewolf.plugins.base.db import global_userinfo_db
from Werewolf.core.bottrack import group_log_db
from config import LOGGER_ID, OWNER_ID


@app.on_message(filters.command("gcast") & filters.user(OWNER_ID))
async def group_broadcast(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("❌ Please provide a message to broadcast.")

    broadcast_text = message.text.split(None, 1)[1]
    sent = 0
    failed = 0

    groups = await group_log_db.find().to_list(length=None)
    total = len(groups)
    estimate = round(total * 0.8)

    status = await message.reply(
        f"📡 Broadcasting to groups...\n"
        f"Total: {total}\n"
        f"Estimated time: ~{estimate}s"
    )

    start_time = time.time()

    for group in groups:
        try:
            await client.send_message(group["_id"], broadcast_text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.8)

    end_time = time.time()
    duration = round(end_time - start_time)

    result = (
        f"✅ <b>Group Broadcast Completed</b>\n\n"
        f"🕒 Time Taken: <code>{duration}s</code>\n"
        f"📬 Sent to: <code>{sent}</code> groups\n"
        f"❌ Failed: <code>{failed}</code>"
    )

    await status.edit(result)
    await client.send_message(LOGGER_ID, result)


@app.on_message(filters.command("ucast") & filters.user(OWNER_ID))
async def user_broadcast(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("❌ Please provide a message to broadcast.")

    broadcast_text = message.text.split(None, 1)[1]
    sent = 0
    failed = 0

    users = await global_userinfo_db.find().to_list(length=None)
    total = len(users)
    estimate = round(total * 0.8)

    status = await message.reply(
        f"📡 Broadcasting to users...\n"
        f"Total: {total}\n"
        f"Estimated time: ~{estimate}s"
    )

    start_time = time.time()

    for user in users:
        try:
            await client.send_message(user["_id"], broadcast_text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.8)

    end_time = time.time()
    duration = round(end_time - start_time)

    result = (
        f"✅ <b>User Broadcast Completed</b>\n\n"
        f"🕒 Time Taken: <code>{duration}s</code>\n"
        f"📬 Sent to: <code>{sent}</code> users\n"
        f"❌ Failed: <code>{failed}</code>"
    )

    await status.edit(result)
    await client.send_message(LOGGER_ID, result)