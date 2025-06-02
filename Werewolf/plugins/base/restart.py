import os
from pyrogram import filters

from Werewolf import app


@app.on_message(filters.command(["restart"]))
async def restart_bot(_, message):
    await message.reply_text("» ʀᴇsᴛᴀʀᴛɪɴɢ ʙᴏᴛ... ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ.")
    os.system(f"kill -9 {os.getpid()} && bash start")
