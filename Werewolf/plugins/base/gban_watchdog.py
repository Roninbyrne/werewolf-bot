from pyrogram import Client
from pyrogram.types import ChatMemberUpdated
from pyrogram.enums import ChatMemberStatus
from Werewolf import app
from Werewolf.plugins.base.db import global_ban_db

@app.on_chat_member_updated()
async def enforce_gban_on_join(client: Client, update: ChatMemberUpdated):
    if update.new_chat_member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED]:
        return

    user = update.new_chat_member.user
    chat = update.chat

    data = global_ban_db.find_one({"_id": user.id})
    if not data or chat.id not in data.get("held_in", []):
        return

    try:
        await client.ban_chat_member(chat.id, user.id)
        global_ban_db.update_one(
            {"_id": user.id},
            {"$pull": {"held_in": chat.id}}
        )
    except:
        pass