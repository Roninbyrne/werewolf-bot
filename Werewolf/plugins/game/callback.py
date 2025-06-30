from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bson import ObjectId

def register_callbacks(app, games_col, players_col, actions_col):

    @app.on_callback_query()
    async def all_callbacks(client, callback):
        data = callback.data
        user_id = callback.from_user.id

        if data.startswith("join_"):
            game_id = ObjectId(data.split("_")[1])
            game = await games_col.find_one({"_id": game_id})
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
            await games_col.update_one({"_id": game_id}, {"$set": {"players": players}})
            await callback.answer(f"✅ Joined! Total: {len(players)}")

        elif data.startswith("reveal_") or data.startswith("bulkrole_"):
            game_id = ObjectId(data.split("_")[1])
            player = await players_col.find_one({"_id": user_id, "game_id": game_id})
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
            player = await players_col.find_one({"_id": user_id})
            game_id = player.get("game_id")
            others = await players_col.find({"game_id": game_id, "_id": {"$ne": user_id}}).to_list(length=100)
            buttons = [
                [InlineKeyboardButton(p.get("name", str(p["_id"])), callback_data=f"target_{action}_{p['_id']}")]
                for p in others
            ]
            await callback.message.edit_text("Select your target:", reply_markup=InlineKeyboardMarkup(buttons))

        elif data.startswith("target_"):
            parts = data.split("_")
            action = parts[1]
            target_id = parts[2]
            player = await players_col.find_one({"_id": user_id})
            chat_id = player.get("game_chat")
            existing = await actions_col.find_one({"chat_id": chat_id, "user_id": user_id, "action": action})
            if existing:
                await actions_col.update_one({"_id": existing["_id"]}, {"$set": {"target_id": target_id}})
            else:
                await actions_col.insert_one({
                    "chat_id": chat_id, "user_id": user_id, "action": action, "target_id": target_id
                })
            await callback.answer("✅ Action submitted.", show_alert=True)
            await callback.message.delete()

        elif data.startswith("vote_"):
            target_id = data.split("_")[1]
            player = await players_col.find_one({"_id": user_id})
            chat_id = player.get("game_chat")
            existing = await actions_col.find_one({"chat_id": chat_id, "user_id": user_id, "action": "vote"})
            if existing:
                await actions_col.update_one({"_id": existing["_id"]}, {"$set": {"target_id": target_id}})
            else:
                await actions_col.insert_one({
                    "chat_id": chat_id, "user_id": user_id, "action": "vote", "target_id": target_id
                })
            await callback.answer("✅ Vote submitted.", show_alert=True)
            await callback.message.delete()

        elif data.startswith("target_wvote_"):
            target_id = int(data.split("_")[2])
            player = await players_col.find_one({"_id": user_id})
            chat_id = player.get("game_chat")
            existing = await actions_col.find_one({"chat_id": chat_id, "user_id": user_id, "action": "wvote"})
            if existing:
                await actions_col.update_one({"_id": existing["_id"]}, {"$set": {"target_id": target_id}})
            else:
                await actions_col.insert_one({
                    "chat_id": chat_id, "user_id": user_id, "action": "wvote", "target_id": target_id
                })
            await callback.answer("✅ Vote cast.", show_alert=True)
            await callback.message.delete()

        elif data.startswith("alpha_bite_"):
            target_id = int(data.split("_")[2])
            player = await players_col.find_one({"_id": user_id})
            chat_id = player.get("game_chat")

            current_bites = await actions_col.find(
                {"chat_id": chat_id, "user_id": user_id, "action": "bite"}
            ).to_list(length=10)

            target_ids = [str(t["target_id"]) for t in current_bites]

            if str(target_id) in target_ids:
                await actions_col.delete_one({
                    "chat_id": chat_id, "user_id": user_id, "action": "bite", "target_id": str(target_id)
                })
            elif len(current_bites) < 2:
                await actions_col.insert_one({
                    "chat_id": chat_id, "user_id": user_id, "action": "bite", "target_id": str(target_id)
                })
            else:
                await callback.answer("❌ You have already selected 2 targets.", show_alert=True)
                return

            others = await players_col.find({"game_id": player["game_id"], "_id": {"$ne": user_id}}).to_list(length=100)
            selected_targets = await actions_col.find({
                "chat_id": chat_id, "user_id": user_id, "action": "bite"
            }).to_list(length=10)

            selected_ids = [str(t["target_id"]) for t in selected_targets]
            buttons = []

            for p in others:
                u = await client.get_users(p["_id"])
                label = f"✅ {u.first_name}" if str(p["_id"]) in selected_ids else u.first_name
                buttons.append([InlineKeyboardButton(label, callback_data=f"alpha_bite_{p['_id']}")])

            try:
                await callback.message.edit_text("🌙 Choose 2 targets to bite:", reply_markup=InlineKeyboardMarkup(buttons))
            except:
                pass

            await callback.answer("✅ Selection updated.")
