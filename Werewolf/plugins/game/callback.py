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
                await callback.answer("❌ Not accepting joins.")
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

        elif data.startswith("nightvote_"):
            game_id = ObjectId(data.split("_")[1])
            game = await games_col.find_one({"_id": game_id})
            player = await players_col.find_one({"_id": user_id, "game_id": game_id})
            if not player or player.get("role") not in ["werewolf", "alpha"]:
                await callback.answer("🧙 You are not a beast.")
                return
            start_link = f"https://t.me/{app.me.username}?start=vote_{game_id}"
            buttons = [[InlineKeyboardButton("🩸 Vote in DM", url=start_link)]]
            await callback.message.edit_text("🔮 Check your DM to vote:", reply_markup=InlineKeyboardMarkup(buttons))
            await callback.answer()

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
            await callback.answer("✅ Action submitted.")
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
            await callback.answer("✅ Vote submitted.")
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
            await callback.answer("✅ Vote cast.")
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
                await callback.answer("❌ You have already selected 2 targets.")
                return

            others = await players_col.find({
                "game_id": player["game_id"], "_id": {"$ne": user_id}
            }).to_list(length=100)
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

        elif data.startswith("dayvote_"):
            parts = data.split("_")
            target_id = int(parts[1])
            game_id = ObjectId(parts[2])

            player = await players_col.find_one({"_id": user_id, "game_id": game_id})
            if not player:
                await callback.answer("❌ You are not allowed to vote.")
                return

            role = player.get("role")
            if role not in ["villager", "spy"]:
                await callback.answer("❌ You are not allowed to vote.")
                return

            chat_id = player.get("game_chat")
            existing = await actions_col.find_one({
                "chat_id": chat_id, "user_id": user_id, "action": "vote_day"
            })
            if existing:
                await actions_col.update_one({"_id": existing["_id"]}, {"$set": {"target_id": target_id}})
            else:
                await actions_col.insert_one({
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "action": "vote_day",
                    "target_id": target_id
                })
            await callback.answer("✅ Vote recorded.")

        elif data.startswith("target_heal_"):
            target_id = int(data.split("_")[2])
            player = await players_col.find_one({"_id": user_id})
            if not player or player.get("role") != "doctor":
                await callback.answer("❌ You are not allowed to heal.")
                return

            chat_id = player.get("game_chat")
            healed_times = player.get("healed_times", 0)

            if user_id == target_id:
                if healed_times % 3 != 0:
                    await callback.answer("❌ You can only heal yourself once every 3 heals.")
                    return
                await players_col.update_one({"_id": user_id}, {"$inc": {"healed_times": 1}})
            else:
                await players_col.update_one({"_id": user_id}, {"$inc": {"healed_times": 1}})

            existing = await actions_col.find_one({"chat_id": chat_id, "user_id": user_id, "action": "heal"})
            if existing:
                await actions_col.update_one({"_id": existing["_id"]}, {"$set": {"target_id": target_id}})
            else:
                await actions_col.insert_one({
                    "chat_id": chat_id, "user_id": user_id, "action": "heal", "target_id": target_id
                })
            await callback.answer("✅ Heal target submitted.")
            await callback.message.delete()
