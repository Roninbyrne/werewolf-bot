from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID
from Werewolf import app
from Werewolf.core.mongo import mongodb

LOGGING_COLLECTION = mongodb.logging_config

async def is_logging_enabled():
    config = await LOGGING_COLLECTION.find_one({"_id": "global"})
    return config and config.get("enabled", False)

@app.on_message(filters.command("logging") & filters.user(OWNER_ID))
async def toggle_logging(client: Client, message: Message):
    config = await LOGGING_COLLECTION.find_one({"_id": "global"}) or {"_id": "global", "enabled": False}
    new_state = not config["enabled"]
    await LOGGING_COLLECTION.update_one({"_id": "global"}, {"$set": {"enabled": new_state}}, upsert=True)

    status = "enabled ✅" if new_state else "disabled ❌"
    await message.reply_text(f"📋 Logging has been {status}.")