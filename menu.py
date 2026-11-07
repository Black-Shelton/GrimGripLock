import os
import random
import time
from aiogram import types, F
from aiogram.types import FSInputFile
import database as db
from cards_data import CARDS
from config import IMG_DIR

COOLDOWN = 3600       # КД призыва (1 час)
BONUS_COOLDOWN = 86400 # КД бонуса (24 часа)

def register_menu_handlers(dp):
    
    # ПРИЗЫВ (Открытие карты)
    @dp.message(
        F.text.lower() == "призыв",
        F.forward_from.is_(None),
        F.forward_from_chat.is_(None),
    )
    async def trigger_card(message: types.Message):
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        player = await db.get_player(user_id, username)
        await db.update_username(user_id, username)
        
        now = time.time()
        if now - player["last_card_time"] < COOLDOWN:
            rem = int(COOLDOWN - (now - player["last_card_time"]))
            await message.reply(f"⏳ Подожди {rem // 60}м {rem % 60}с")
            return
            
        total_chance = sum(c["chance"] for c in CARDS)
        roll = random.uniform(0, total_chance)
        current = 0
        card = CARDS[-1]
        for c in CARDS:
            current += c["chance"]
            if roll <= current:
                card = c
                break
                
        is_new = await db.add_to_inventory(user_id, card["name"])
        total_count = await db.get_card_count(user_id, card["name"])
        await db.set_last_card_time(user_id, now)
        
        status = "🆕 Новая карта!" if is_new else "♻️ Дубликат"
        
        caption = (
            f"{status}\n\n"
            f"🎴 Карта: <b>{card['name']}</b>\n"
            f"У тебя: <b>×{total_count}</b>"
        )
        
        media_path = os.path.join(IMG_DIR, card.get("file", ""))
        if os.path.exists(media_path):
            await message.reply_photo(photo=FSInputFile(media_path), caption=caption, parse_mode="HTML")
        else:
            await message.reply(caption, parse_mode="HTML")

    # БОНУС
    @dp.message(F.text.lower() == "бонус")
    async def cmd_bonus(message: types.Message):
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        player = await db.get_player(user_id, username)
        await db.update_username(user_id, username)
        
        now = time.time()
        if now - player["last_bonus_time"] < BONUS_COOLDOWN:
            rem = int(BONUS_COOLDOWN - (now - player["last_bonus_time"]))
            await message.reply(f"⏳ Бонус будет доступен через {rem // 3600}ч {(rem % 3600) // 60}м")
            return
            
        coins = random.randint(100, 500)
        await db.add_balance(user_id, coins)
        await db.set_last_bonus_time(user_id, now)
        
        new_bal = player["balance"] + coins
        await message.reply(f"🎁 <b>Бонус!</b>\n\n+{coins} 🪙\nБаланс: <b>{new_bal}</b> 🪙", parse_mode="HTML")

    # ПРОФИЛЬ (чтобы смотреть баланс)
    @dp.message(F.text.lower() == "профиль")
    async def cmd_profile(message: types.Message):
        player = await db.get_player(message.from_user.id, message.from_user.username)
        await message.answer(f"👤 <b>Профиль</b>\n\nМонеты: <b>{player['balance']}</b> 🪙", parse_mode="HTML")