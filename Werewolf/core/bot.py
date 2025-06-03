from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus, ParseMode

import config
from ..logging import LOGGER

app = Client(
    name="Security",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    in_memory=True,
    parse_mode=ParseMode.HTML,
    max_concurrent_transmissions=7,
    update_chat_members=True
)

async def start_bot():
    await app.start()
    me = await app.get_me()
    app.id = me.id
    app.name = me.first_name + " " + (me.last_name or "")
    app.username = me.username
    app.mention = me.mention

    try:
        await app.send_message(
            chat_id=config.LOGGER_ID,
            text=f"<u><b>» {app.mention} ʙᴏᴛ sᴛᴀʀᴛᴇᴅ :</b></u>\n\nɪᴅ : <code>{app.id}</code>\nɴᴀᴍᴇ : {app.name}\nᴜsᴇʀɴᴀᴍᴇ : @{app.username}",
        )
    except (errors.ChannelInvalid, errors.PeerIdInvalid):
        LOGGER(__name__).error(
            "Bot has failed to access the log group/channel. Make sure that you have added your bot to your log group/channel."
        )
        exit()
    except Exception as ex:
        LOGGER(__name__).error(
            f"Bot has failed to access the log group/channel.\n  Reason : {type(ex).__name__}."
        )
        exit()

    status = await app.get_chat_member(config.LOGGER_ID, app.id)
    if status.status != ChatMemberStatus.ADMINISTRATOR:
        LOGGER(__name__).error(
            "Please promote your bot as an admin in your log group/channel."
        )
        exit()

    LOGGER(__name__).info(f"Bot Started as {app.name}")