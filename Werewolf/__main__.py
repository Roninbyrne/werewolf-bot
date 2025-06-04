import asyncio
import importlib
from pyrogram import idle

from Werewolf import LOGGER, app, start_bot
from Werewolf.plugins import ALL_MODULES
from Werewolf.plugins.bottrack import verify_groups_command
from config import OWNER_ID

async def init():
    await start_bot()
    for all_module in ALL_MODULES:
        importlib.import_module("Werewolf.plugins" + all_module)
    LOGGER("Werewolf.plugins").info("Successfully Imported Modules...")
    LOGGER("Werewolf").info("Werewolf Game Bot Started Successfully.")

    try:
        from pyrogram.types import User
        dummy_message = type("Dummy", (), {
            "from_user": type("FromUser", (), {"id": OWNER_ID}),
            "reply_text": lambda *args, **kwargs: None
        })()
        await verify_groups_command(app, dummy_message)
    except Exception as e:
        LOGGER("Werewolf").warning(f"Failed to verify groups on startup: {e}")

    await idle()
    await app.stop()
    LOGGER("Werewolf").info("Stopping Werewolf Game Bot...")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())