from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pymongo import MongoClient
from config import MONGO_DB_URI, LOGGER_ID

from Werewolf import app
from Werewolf.core.mongo import mongodb

mongo_client = MongoClient(MONGO_DB_URI)
group_log_db = mongo_client["Logs"]["group_logs"]

@app.on_chat_member_updated()
async def log_group_events(client, chat_member):
    bot_id = (await client.get_me()).id
    if chat_member.new_chat_member.user.id != bot_id:
        return

    chat = chat_member.chat
    group_id = chat.id

    if chat_member.new_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]:
        try:
            invite_link = await client.export_chat_invite_link(group_id)
        except:
            invite_link = "Not available"

        try:
            member_count = await client.get_chat_members_count(group_id)
        except:
            member_count = "Unknown"

        group_info = {
            "_id": group_id,
            "title": chat.title,
            "username": chat.username,
            "link": invite_link,
            "dc_id": chat.dc_id,
            "members": member_count
        }

        group_log_db.update_one({"_id": group_id}, {"$set": group_info}, upsert=True)

        text = (
            f"✅ <b>Bot added to group</b>\n\n"
            f"📌 <b>Group Name:</b> {chat.title}\n"
            f"🆔 <b>Group ID:</b> <code>{group_id}</code>\n"
            f"🔗 <b>Group Link:</b> {invite_link}\n"
            f"🌐 <b>DC ID:</b> {chat.dc_id}\n"
            f"👥 <b>Members:</b> {member_count}"
        )
        await client.send_message(LOGGER_ID, text)

    elif chat_member.new_chat_member.status == ChatMemberStatus.LEFT:
        group_log_db.delete_one({"_id": group_id})
        text = (
            f"❌ <b>Bot removed from group</b>\n\n"
            f"📌 <b>Group Name:</b> {chat.title}\n"
            f"🆔 <b>Group ID:</b> <code>{group_id}</code>"
        )
        await client.send_message(LOGGER_ID, text)