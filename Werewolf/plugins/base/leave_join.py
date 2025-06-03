from pyrogram import Client
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.types import ChatMemberUpdated
from Werewolf.plugins.base.db import group_log_db
from config import LOGGER_ID
import asyncio
import traceback

from Werewolf import app
from Werewolf.plugins.base.logging_toggle import is_logging_enabled


@app.on_chat_member_updated()
async def log_group_events(client: Client, chat_member: ChatMemberUpdated):
    try:
        bot_id = (await client.get_me()).id
        new_member = chat_member.new_chat_member
        old_member = chat_member.old_chat_member

        if not (new_member and new_member.user and new_member.user.id == bot_id):
            print("[SKIP] Not a bot join event.")
            return

        chat = chat_member.chat
        group_id = chat.id

        if chat.type != ChatType.SUPERGROUP:
            print(f"[SKIP] Not a supergroup: {group_id}")
            return

        if (old_member is None or old_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]) and \
           new_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]:

            print(f"[INFO] Bot added to group: {chat.title} ({group_id})")

            try:
                invite_link = await client.export_chat_invite_link(group_id)
            except Exception as e:
                invite_link = "Not available"
                print(f"[WARN] Failed to get invite link: {e}")

            try:
                member_count = (await client.get_chat(group_id)).members_count
            except Exception as e:
                member_count = "Unknown"
                print(f"[WARN] Failed to get member count: {e}")

            group_info = {
                "_id": group_id,
                "title": chat.title,
                "username": chat.username,
                "link": invite_link,
                "members": member_count
            }

            try:
                result = await group_log_db.update_one(
                    {"_id": group_id}, {"$set": group_info}, upsert=True
                )
                print(f"[DB] Group info saved: {result.raw_result}")
            except Exception as e:
                print(f"[ERROR] Failed to save group info to DB: {e}")
                traceback.print_exc()

            if await is_logging_enabled():
                text = (
                    f"✅ <b>Bot added to group</b>\n\n"
                    f"📌 <b>Group Name:</b> {chat.title}\n"
                    f"🆔 <b>Group ID:</b> <code>{group_id}</code>\n"
                    f"🔗 <b>Group Link:</b> {invite_link}\n"
                    f"👤 <b>Username:</b> @{chat.username or 'None'}\n"
                    f"👥 <b>Members:</b> {member_count}"
                )
                await client.send_message(LOGGER_ID, text)
    except Exception as e:
        print(f"[FATAL ERROR] in log_group_events: {e}")
        traceback.print_exc()


async def check_bot_removal():
    await asyncio.sleep(10)
    bot = await app.get_me()
    print("[INFO] Started bot removal checker loop.")

    while True:
        try:
            cursor = group_log_db.find()
            async for group in cursor:
                group_id = group["_id"]
                try:
                    member = await app.get_chat_member(group_id, bot.id)
                    if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
                        print(f"[INFO] Bot has been removed from: {group_id}")
                        await group_log_db.delete_one({"_id": group_id})
                        print(f"[DB] Group {group_id} removed from DB.")

                        if await is_logging_enabled():
                            text = (
                                f"❌ <b>Bot removed from group</b>\n\n"
                                f"📌 <b>Group Name:</b> {group.get('title', 'Unknown')}\n"
                                f"🆔 <b>Group ID:</b> <code>{group_id}</code>\n"
                                f"👤 <b>Username:</b> @{group.get('username') or 'None'}"
                            )
                            await app.send_message(LOGGER_ID, text)
                    else:
                        print(f"[OK] Bot is still in group: {group_id}")
                except Exception as e:
                    print(f"[ERROR] Checking group {group_id} failed: {e}")
                    traceback.print_exc()
                await asyncio.sleep(1)
        except Exception as e:
            print(f"[FATAL ERROR] in check_bot_removal loop: {e}")
            traceback.print_exc()

        await asyncio.sleep(10)


def start_removal_monitor():
    print("[INIT] Starting bot removal monitor...")
    asyncio.create_task(check_bot_removal())