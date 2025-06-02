import asyncio
import importlib
from pyrogram import idle

from Werewolf import LOGGER, app
from Werewolf.plugins import ALL_MODULES
from Werewolf.plugins.base.leave_join import start_removal_monitor
from Werewolf.plugins.base.userinfo import setup_user_tracking


async def init():
    await app.start()
    setup_user_tracking(app)
    start_removal_monitor()
    for all_module in ALL_MODULES:
        importlib.import_module("Werewolf.plugins" + all_module)
    LOGGER("Werewolf.plugins").info("Successfully Imported Modules...")
    LOGGER("Werewolf").info("Werewolf Game Bot Started Successfully.")
    await idle()
    await app.stop()
    LOGGER("Werewolf").info("Stopping Werewolf Game Bot...")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())