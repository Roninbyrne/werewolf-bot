import asyncio
import importlib

from pyrogram import idle

import config
from Werewolf import LOGGER, app
from Werewolf.misc import sudo
from Werewolf.plugins import ALL_MODULES
from Werewolf.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS


async def init():
    await sudo()
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass
    await app.start()
    for all_module in ALL_MODULES:
        importlib.import_module("Werewolf.plugins" + all_module)
    LOGGER("Werewolf.plugins").info("Successfully Imported Modules...")
    LOGGER("Werewolf").info("Werewolf Game Bot Started Successfully.")
    await idle()
    await app.stop()
    LOGGER("Werewolf").info("Stopping Security Bot...")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
