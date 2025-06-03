import asyncio
import importlib
from pyrogram import idle

from Werewolf import LOGGER, app, start_bot
from Werewolf.plugins import ALL_MODULES

async def init():
    await start_bot()
    for all_module in ALL_MODULES:
        importlib.import_module("Werewolf.plugins" + all_module)
    LOGGER("Werewolf.plugins").info("Successfully Imported Modules...")
    LOGGER("Werewolf").info("Werewolf Game Bot Started Successfully.")
    await idle()
    await app.stop()
    LOGGER("Werewolf").info("Stopping Werewolf Game Bot...")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())