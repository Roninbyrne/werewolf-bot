from Werewolf import app
from pyrogram import filters
from pyrogram.enums import ParseMode
from datetime import datetime
import asyncio
import random
from bson import ObjectId
from config import MONGO_DB_URI
from werewolf.plugins.game.callbacks import register_callbacks
from Werewolf.core.mongo import games_col, players_col, actions_col
from config import (
    JOIN_TIME,
    MIN_PLAYERS,
    MAX_PLAYERS,
    ROLE_WEREWOLF,
    ROLE_VILLAGER,
    ROLE_ALPHA,
    ROLE_DOCTOR,
    ROLE_SPY,
)

register_callbacks(app, games_col, players_col, actions_col)

@app.on_message(filters.command("startgame") & filters.group)
async def start_game(client, message):
    chat_id = message.chat.id
    if await games_col.find_one({"chat_id": chat_id, "active": True}):
        await message.reply("❌ Game already running. Use /stopgame to stop.")
        return

    game_data = {
        "chat_id": chat_id,
        "active": True,
        "players": [],
        "phase": "lobby",
        "start_time": datetime.utcnow(),
        "day_night": "day",
    }
    game_id = (await games_col.insert_one(game_data)).inserted_id

    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("📝 Join Game", callback_data=f"join_{game_id}")]]
    )
    await message.reply(
        f"🎲 Game started! Join in {JOIN_TIME} seconds (min {MIN_PLAYERS}, max {MAX_PLAYERS}).",
        reply_markup=keyboard,
    )
    await asyncio.sleep(JOIN_TIME)

    game = await games_col.find_one({"_id": game_id})
    players = game.get("players", [])
    if len(players) < MIN_PLAYERS:
        await games_col.update_one({"_id": game_id}, {"$set": {"active": False, "phase": "cancelled"}})
        await client.send_message(chat_id, f"❌ Not enough players ({len(players)}/{MIN_PLAYERS}). Game cancelled.")
        return

    roles = generate_roles(len(players))
    for pid, role in zip(players, roles):
        await players_col.update_one({"_id": pid}, {"$set": {
            "role": role,
            "game_id": game_id,
            "game_chat": chat_id,
            "disguised": False,
            "healed_times": 0
        }}, upsert=True)

    await games_col.update_one({"_id": game_id}, {"$set": {"phase": "started"}})
    player_lines = []
    for i, pid in enumerate(players):
        user = await client.get_users(pid)
        player_lines.append(f"{i+1}. [{user.first_name}](tg://user?id={pid})")

    await client.send_message(
        chat_id,
        f"✅ Game started with {len(players)} players!\n" + "\n".join(player_lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("CHECK UR ROLE", callback_data=f"bulkrole_{game_id}")]])
    )

    asyncio.create_task(day_night_cycle(chat_id, game_id))
    for pid in players:
        try:
            await client.send_message(
                pid,
                "🎭 Game started! Press below to reveal your role.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Reveal Role", callback_data=f"reveal_{game_id}")]])
            )
        except:
            user = await client.get_users(pid)
            await client.send_message(
                chat_id,
                f"⚠️ Couldn't DM [{user.first_name}](tg://user?id={pid}). Ask them to start the bot in private chat.",
                parse_mode=ParseMode.MARKDOWN
            )

@app.on_message(filters.command("stopgame") & filters.group)
async def stop_game(client, message):
    chat_id = message.chat.id
    game = await games_col.find_one({"chat_id": chat_id, "active": True})
    if not game:
        await message.reply("❌ No active game.")
        return
    await reset_game(chat_id)
    await message.reply("🛑 Game stopped by admin.")

@app.on_message(filters.group & filters.text & ~filters.service)
async def suppress_messages_at_night(client, message):
    chat_id = message.chat.id
    game = await games_col.find_one({"chat_id": chat_id, "active": True})
    if not game or game.get("phase") != "started":
        return
    if game.get("day_night") == "night":
        await message.delete()

async def reset_game(chat_id):
    await games_col.update_one({"chat_id": chat_id, "active": True}, {"$set": {"active": False, "phase": "stopped"}})
    await players_col.update_many({"game_chat": chat_id}, {"$unset": {
        "role": "", "game_id": "", "disguised": "", "healed_times": "", "spy_once_used": ""
    }})
    await actions_col.delete_many({"chat_id": chat_id})

def generate_roles(num):
    roles = []
    if num >= 8:
        roles.append(ROLE_ALPHA)
        roles.append(ROLE_DOCTOR)
        roles.append(ROLE_SPY)
        werewolves = max(1, (num - 3) // 4)
        villagers = num - (werewolves + 3)
        roles.extend([ROLE_WEREWOLF] * werewolves)
        roles.extend([ROLE_VILLAGER] * villagers)
    else:
        werewolves = max(1, num // 4)
        villagers = num - werewolves
        roles = [ROLE_WEREWOLF] * werewolves + [ROLE_VILLAGER] * villagers
    random.shuffle(roles)
    return roles

async def count_roles(game_id):
    players = await players_col.find({"game_id": game_id}).to_list(length=100)
    role_counts = {ROLE_WEREWOLF: 0, ROLE_ALPHA: 0, ROLE_VILLAGER: 0}
    for p in players:
        role = p.get("role")
        if role in role_counts:
            role_counts[role] += 1
    return role_counts

async def check_win_condition(chat_id, game_id):
    roles = await count_roles(game_id)
    if roles[ROLE_WEREWOLF] + roles[ROLE_ALPHA] == 0:
        await app.send_message(chat_id, "🎉 Villagers have eliminated all werewolves! They win!")
        await reset_game(chat_id)
    elif roles[ROLE_VILLAGER] == 0:
        await app.send_message(chat_id, "🐺 Werewolves dominate the village! They win!")
        await reset_game(chat_id)

async def day_night_cycle(chat_id, game_id):
    from game.logic import night_phase_logic, day_phase_logic
    while True:
        game = await games_col.find_one({"_id": game_id, "active": True})
        if not game:
            break
        current_phase = game.get("day_night", "day")
        next_phase = "night" if current_phase == "day" else "day"
        await games_col.update_one({"_id": game_id}, {"$set": {"day_night": next_phase}})
        await app.send_message(chat_id, f"🌗 It's now {next_phase.upper()} time!", parse_mode=ParseMode.MARKDOWN)
        if next_phase == "night":
            await night_phase_logic(chat_id, game_id, app, players_col, actions_col)
        else:
            await day_phase_logic(chat_id, game_id, app, players_col, actions_col, games_col)
        await asyncio.sleep(60)

if __name__ == "__main__":
    app.run()
