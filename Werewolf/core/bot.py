from pyrogram import Client
from pyrogram.enums import ParseMode

import config
from ..logging import LOGGER

app = Client(
    name="Werewolf",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    parse_mode=ParseMode.HTML,
    max_concurrent_transmissions=7
)

async def start_bot():
    await app.start()
    me = await app.get_me()
    app.id = me.id
    app.name = me.first_name + " " + (me.last_name or "")
    app.username = me.username
    app.mention = me.mention

    LOGGER(__name__).info(f"Bot Started as {app.name} (@{app.username})")