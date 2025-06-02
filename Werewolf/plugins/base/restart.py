import os
import logging
from pyrogram import filters
from Werewolf import app
from config import OWNER_ID

logging.basicConfig(
    format='[%(asctime)s] [%(levelname)s] - %(message)s',
    level=logging.INFO
)

@app.on_message(filters.command("restart") & filters.user(OWNER_ID))
async def restart_bot(_, message):
    logging.info(f"Restart command received from {message.from_user.id}")
    await message.reply_text("🔄 Restarting bot... Please wait.")
    logging.info("Shutting down process for restart...")
    os.system(f"kill -9 {os.getpid()} && bash start")