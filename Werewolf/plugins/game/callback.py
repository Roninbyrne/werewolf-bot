from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bson import ObjectId
import random
import asyncio

def register_callbacks(app, games_col, players_col, actions_col):

    @app.on_callback_query()
    async def all_callbacks(client, callback):
        data = callback.data
        user_id = callback.from_user.id

        if data.startswith("join_"):
            game_id = ObjectId(data.split("_")[1])
            game = games_col.find_one({"_id": game_id})
            if not game or not game.get("active") or game.get("phase") != "lobby":
                await callback.answer("❌ Not accepting joins.", show_alert=True)
                return
            players = game.get("players", [])
            if user_id in players:
                await callback.answer("✅ Already joined.")
                return
            if len(players) >= 20:
                await callback.answer("❌ Game full.")
                return
            players.append(user_id)
            games_col.update_one({"_id": game_id}, {"$set": {"players": players}})
            await callback.answer(f"✅ Joined! Total: {len(players)}")

        elif data.startswith("reveal_") or data.startswith("bulkrole_"):
            game_id = ObjectId(data.split("_")[1])
            player = players_col.find_one({"_id": user_id, "game_id": game_id})
            if not player:
                await callback.answer("❌ You are not part of this game.", show_alert=True)
                return
            role = player.get("role", "Unknown").capitalize()
            disguised = player.get("disguised", False)
            text = f"🎭 Role: *{role}*\n"
            if disguised:
                text += "🕵️‍♂️ You are currently disguised."
            await callback.answer()
            await callback.message.edit_text(text, parse_mode=ParseMode.MARKDOWN)

        elif data.startswith("action_"):
            action = data.split("_")[1]
            player = players_col.find_one({"_id": user_id})
            game_id = player.get("game_id")
            others = list(players_col.find({"game_id": game_id, "_id": {"$ne": user_id}}))
            buttons = [
                [InlineKeyboardButton(p.get("name", str(p["_id"])), callback_data=f"target_{action}_{p['_id']}")]
                for p in others
            ]
            await callback.message.edit_text("Select your target:", reply_markup=InlineKeyboardMarkup(buttons))

        elif data.startswith("target_"):
            parts = data.split("_")
            action = parts[1]
            target_id = parts[2]
            player = players_col.find_one({"_id": user_id})
            chat_id = player.get("game_chat")
            existing = actions_col.find_one({"chat_id": chat_id, "user_id": user_id, "action": action})
            if existing:
                actions_col.update_one({"_id": existing["_id"]}, {"$set": {"target_id": target_id}})
            else:
                actions_col.insert_one({
                    "chat_id": chat_id, "user_id": user_id, "action": action, "target_id": target_id
                })
            await callback.answer("✅ Action submitted.", show_alert=True)
            await callback.message.delete()

        elif data.startswith("vote_"):
            target_id = data.split("_")[1]
            player = players_col.find_one({"_id": user_id})
            chat_id = player.get("game_chat")
            existing = actions_col.find_one({"chat_id": chat_id, "user_id": user_id, "action": "vote"})
            if existing:
                actions_col.update_one({"_id": existing["_id"]}, {"$set": {"target_id": target_id}})
            else:
                actions_col.insert_one({
                    "chat_id": chat_id, "user_id": user_id, "action": "vote", "target_id": target_id
                })
            await callback.answer("✅ Vote submitted.", show_alert=True)
            await callback.message.delete()

        elif data.startswith("target_wvote_"):
            target_id = int(data.split("_")[2])
            player = players_col.find_one({"_id": user_id})
            chat_id = player.get("game_chat")
            existing = actions_col.find_one({"chat_id": chat_id, "user_id": user_id, "action": "wvote"})
            if existing:
                actions_col.update_one({"_id": existing["_id"]}, {"$set": {"target_id": target_id}})
            else:
                actions_col.insert_one({
                    "chat_id": chat_id, "user_id": user_id, "action": "wvote", "target_id": target_id
                })
            await callback.answer("✅ Vote cast.", show_alert=True)
            await callback.message.delete()

        elif data.startswith("alpha_bite_"):
            target_id = int(data.split("_")[2])
            player = players_col.find_one({"_id": user_id})
            chat_id = player.get("game_chat")
            existing = actions_col.count_documents({"chat_id": chat_id, "user_id": user_id, "action": "bite"})
            if existing < 2:
                actions_col.insert_one({
                    "chat_id": chat_id, "user_id": user_id, "action": "bite", "target_id": target_id
                })
                await callback.answer("✅ Bite target selected.", show_alert=True)
            else:
                await callback.answer("❌ You have already selected 2 targets.", show_alert=True)
            await callback.message.delete()
