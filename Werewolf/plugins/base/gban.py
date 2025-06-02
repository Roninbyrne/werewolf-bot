from pyrogram import Client, filters
from pyrogram.errors import UserAdminInvalid, ChatAdminRequired, UserNotParticipant
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from Werewolf import app
from Werewolf.plugins.base.db import group_log_db, global_ban_db
from config import OWNER_ID, GBAN_LOGS
import asyncio
import time


@app.on_message(filters.command("gban") & filters.user(OWNER_ID))
async def gban_user(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply("Usage: /gban user_id | username | reply to user\nOptionally add reason.")

    await message.delete()

    if message.reply_to_message:
        user = message.reply_to_message.from_user
        reason = message.text.split(None, 1)[1] if len(message.text.split()) > 1 else "No reason provided"
    else:
        args = message.text.split(None, 2)
        user = await client.get_users(args[1])
        reason = args[2] if len(args) > 2 else "No reason provided"

    user_id = user.id

    if await global_ban_db.find_one({"_id": user_id}):
        return await client.send_message(message.chat.id, f"🚫 <b>User is already globally banned.</b>\n🆔 <code>{user_id}</code>")

    username = f"@{user.username}" if user.username else "N/A"
    name = f"{user.first_name} {user.last_name or ''}".strip()
    initiator = message.from_user
    initiator_name = initiator.first_name

    group_count = await group_log_db.count_documents({})
    estimated_time = round(group_count * 0.5, 2)

    status_msg = await client.send_message(
        message.chat.id,
        f"🔄 <b>Imposing Global Ban...</b>\n"
        f"👮‍♂️ <b>Initiated by:</b> {initiator_name}\n"
        f"🚫 <b>Target:</b> {name}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"📄 <b>Reason:</b> {reason}\n"
        f"⏳ <b>Estimated time:</b> {estimated_time}s"
    )

    banned_in = 0
    held_in = 0
    start_time = time.time()

    cursor = group_log_db.find()
    async for group in cursor:
        group_id = group["_id"]
        try:
            await client.get_chat_member(group_id, user_id)
        except (UserNotParticipant, Exception):
            await global_ban_db.update_one(
                {"_id": user_id}, {"$addToSet": {"held_in": group_id}}, upsert=True
            )
            held_in += 1
            continue

        try:
            await client.ban_chat_member(group_id, user_id)
            banned_in += 1
        except (UserAdminInvalid, ChatAdminRequired):
            await global_ban_db.update_one(
                {"_id": user_id}, {"$addToSet": {"held_in": group_id}}, upsert=True
            )
            held_in += 1

            db_user = await global_ban_db.find_one({"_id": user_id}) or {}
            alerts = db_user.get("alerts", {})
            disabled_alerts = db_user.get("alerts_disabled", [])
            now_ts = int(time.time())
            last_alert = alerts.get(str(group_id), 0)

            if group_id in disabled_alerts:
                continue

            if now_ts - last_alert >= 86400:
                try:
                    await client.send_message(
                        group_id,
                        f"#Alert\n🚨 This user has been globally banned.\n"
                        f"👤 <b>User:</b> {name} ({user_id})\n"
                        f"📄 <b>Reason:</b> {reason}",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔕 Stop Future Alerts", callback_data=f"stop_alert:{user_id}")]
                        ])
                    )
                    alerts[str(group_id)] = now_ts
                    await global_ban_db.update_one({"_id": user_id}, {"$set": {"alerts": alerts}})
                except:
                    pass
            continue

        await asyncio.sleep(0.5)

    await global_ban_db.update_one(
        {"_id": user_id},
        {
            "$set": {
                "name": name,
                "username": user.username,
                "reason": reason,
                "banned_by": initiator.id,
                "banned_in": banned_in,
                "timestamp": int(time.time())
            }
        },
        upsert=True
    )

    duration = round(time.time() - start_time, 2)

    final_text = (
        f"✅ <b>Global Ban Completed</b>\n\n"
        f"👤 <b>User:</b> {name}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🔨 <b>Banned in:</b> {banned_in} groups\n"
        f"⏸️ <b>Hold in:</b> {held_in} groups\n"
        f"📄 <b>Reason:</b> {reason}\n"
        f"⏱️ <b>Time taken:</b> {duration}s"
    )

    await status_msg.delete()
    await client.send_message(message.chat.id, final_text)
    await client.send_message(GBAN_LOGS, final_text)


@app.on_callback_query(filters.regex(r"stop_alert:(\d+)"))
async def stop_gban_alerts(client: Client, callback_query):
    user_id = int(callback_query.data.split(":")[1])
    group_id = callback_query.message.chat.id

    db_user = await global_ban_db.find_one({"_id": user_id}) or {}
    disabled_alerts = db_user.get("alerts_disabled", [])

    if group_id not in disabled_alerts:
        disabled_alerts.append(group_id)
        await global_ban_db.update_one(
            {"_id": user_id},
            {"$set": {"alerts_disabled": disabled_alerts}},
            upsert=True
        )

    await callback_query.answer("🔕 Alerts disabled for this user in this group.", show_alert=True)
    await callback_query.message.edit_reply_markup(reply_markup=None)