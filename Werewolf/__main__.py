import asyncio
import importlib
from pyrogram import idle
from Werewolf import LOGGER, app, start_bot
from Werewolf.plugins import ALL_MODULES
from Werewolf.core.bottrack import verify_groups_command
from config import OWNER_ID

class DummyUser:
    id = OWNER_ID

class DummyMessage:
    from_user = DummyUser()

    async def reply_text(self, *args, **kwargs):
        pass

async def init():
    await start_bot()

    for all_module in ALL_MODULES:
        importlib.import_module("Werewolf.plugins." + all_module)
    LOGGER("Werewolf.plugins").info("✅ Successfully imported all modules.")

    try:
        dummy_message = DummyMessage()
        await verify_groups_command(app, dummy_message)
        LOGGER("Werewolf").info("🔁 Automatically verified groups on startup.")
    except Exception as e:
        LOGGER("Werewolf").warning(f"⚠️ Failed to verify groups on startup: {e}")

    LOGGER("Werewolf").info("🚀 Werewolf Game Bot Started Successfully.")
    await idle()

    await app.stop()
    LOGGER("Werewolf").info("🛑 Stopping Werewolf Game Bot...")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())