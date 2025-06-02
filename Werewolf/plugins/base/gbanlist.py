from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import filters, Client
from Werewolf import app
from Werewolf.plugins.base.db import global_ban_db
from config import OWNER_ID

PER_PAGE = 10

def format_gban_list(data, page):
    start = page * PER_PAGE
    end = start + PER_PAGE
    lines = []

    for i, user in enumerate(data[start:end], start=1 + start):
        name = user.get("name", "N/A")
        user_id = user["_id"]
        reason = user.get("reason", "No reason provided")
        lines.append(f"{i}. <b>{name}</b> [<code>{user_id}</code>]\n   📄 <i>{reason}</i>")

    text = f"🚫 <b>Global Ban List</b> ({len(data)} users)\n\n" + "\n\n".join(lines)
    return text

def get_gban_keyboard(current_page, total_pages):
    buttons = []
    if total_pages > 1:
        row = []
        if current_page > 0:
            row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"gbanlist:{current_page - 1}"))
        if current_page < total_pages - 1:
            row.append(InlineKeyboardButton("Next ➡️", callback_data=f"gbanlist:{current_page + 1}"))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons) if buttons else None

@app.on_message(filters.command("gbanlist") & filters.user(OWNER_ID))
async def show_gban_list(client: Client, message: Message):
    data = list(global_ban_db.find({"banned_by": OWNER_ID}))
    if not data:
        return await message.reply("✅ No users are currently globally banned by you.")

    page = 0
    total_pages = (len(data) + PER_PAGE - 1) // PER_PAGE
    text = format_gban_list(data, page)
    keyboard = get_gban_keyboard(page, total_pages)

    await message.reply(text, reply_markup=keyboard, disable_web_page_preview=True)

@app.on_callback_query(filters.regex(r"gbanlist:(\d+)") & filters.user(OWNER_ID))
async def paginate_gban_list(client: Client, query: CallbackQuery):
    page = int(query.data.split(":")[1])
    data = list(global_ban_db.find({"banned_by": OWNER_ID}))
    total_pages = (len(data) + PER_PAGE - 1) // PER_PAGE

    if page >= total_pages:
        return await query.answer("No more pages.", show_alert=True)

    text = format_gban_list(data, page)
    keyboard = get_gban_keyboard(page, total_pages)

    await query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    await query.answer()