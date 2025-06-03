from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import Message
from Werewolf import app
from Werewolf.plugins.base.db import global_ban_db
from Werewolf.core.bottrack import group_log_db
from config import OWNER_ID, GBAN_LOGS
import asyncio

@app.on_message(filters.command("ungban") & filters.user(OWNER_ID))
async def ungban_user(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply("Usage: /ungban user_id | username | reply to user")

    await message.delete()

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        args = message.text.split(None, 1)
        user = await client.get_users(args[1])

    user_id = user.id
    name = f"{user.first_name} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else "N/A"

    initiator = message.from_user
    initiator_name = initiator.first_name
    initiator_id = initiator.id

    unbanned_in = 0
    async for group in group_log_db.find():
        group_id = group["_id"]
        try:
            await client.unban_chat_member(group_id, user_id)
            unbanned_in += 1
        except:
            continue
        await asyncio.sleep(0.5)

    global_ban_db.delete_one({"_id": user_id})

    text = (
        f"✅ <b>Global Unban Successful</b>\n\n"
        f"👤 <b>User:</b> {name}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🔓 <b>Unbanned in:</b> {unbanned_in} groups\n"
        f"👮‍♂️ <b>Globally unbanned by:</b> {initiator_name} [<code>{initiator_id}</code>]"
    )

    await client.send_message(message.chat.id, text)
    await client.send_message(GBAN_LOGS, text)