from aiogram import types, F
import database as db
from config import ADMIN_IDS
from cards_data import find_card_by_name

def is_admin(user_id):
    return user_id in ADMIN_IDS

def register_admin_handlers(dp):
    
    @dp.message(F.text.lower().startswith("вд монеты"))
    async def give_coins(message: types.Message):
        if not is_admin(message.from_user.id): return
        parts = message.text.split()
        
        if message.reply_to_message:
            if len(parts) != 3: return await message.reply("❌ вд монеты 100 (ответом)")
            amount = int(parts[2])
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
            await db.get_player(target_id, message.reply_to_message.from_user.username)
        else:
            if len(parts) != 4 or not parts[2].startswith("@"): return await message.reply("❌ вд монеты @user 100")
            amount = int(parts[3])
            target = await db.find_player_by_username(parts[2][1:])
            if not target: return await message.reply("❌ Игрок не найден")
            target_id, target_name = target["user_id"], target["username"]
            
        await db.add_balance(target_id, amount)
        await message.reply(f"✅ Выдано <b>{amount}</b> 🪙 игроку <b>{target_name}</b>", parse_mode="HTML")

    @dp.message(F.text.lower().startswith("вд карту"))
    async def give_card(message: types.Message):
        if not is_admin(message.from_user.id): return
        rest = message.text[len("вд карту"):].strip()
        
        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
            await db.get_player(target_id, message.reply_to_message.from_user.username)
            card_name = rest.strip('"').strip("'")
        else:
            parts = rest.split(maxsplit=1)
            if len(parts) < 2 or not parts[0].startswith("@"): return await message.reply("❌ вд карту @user \"название\"")
            target = await db.find_player_by_username(parts[0][1:])
            if not target: return await message.reply("❌ Игрок не найден")
            target_id, target_name = target["user_id"], target["username"]
            card_name = parts[1].strip('"').strip("'")
            
        card = find_card_by_name(card_name)
        if not card: return await message.reply(f"❌ Карта «{card_name}» не найдена")
        
        await db.add_to_inventory(target_id, card["name"])
        total = await db.get_card_count(target_id, card["name"])
        await message.reply(f"✅ Выдана <b>{card['name']}</b> игроку <b>{target_name}</b>\nУ него: <b>×{total}</b>", parse_mode="HTML")

    @dp.message(F.text.lower().startswith("забрать карту"))
    async def take_card(message: types.Message):
        if not is_admin(message.from_user.id): return
        rest = message.text[len("забрать карту"):].strip()
        
        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
            card_name = rest.strip('"').strip("'")
        else:
            parts = rest.split(maxsplit=1)
            if len(parts) < 2 or not parts[0].startswith("@"): return await message.reply("❌ забрать карту @user \"название\"")
            target = await db.find_player_by_username(parts[0][1:])
            if not target: return await message.reply("❌ Игрок не найден")
            target_id, target_name = target["user_id"], target["username"]
            card_name = parts[1].strip('"').strip("'")
            
        count = await db.get_card_count(target_id, card_name)
        if count <= 0: return await message.reply(f"❌ У игрока нет карты «{card_name}»")
        
        await db.remove_from_inventory(target_id, card_name)
        new_count = await db.get_card_count(target_id, card_name)
        await message.reply(f"✅ Забрана <b>{card_name}</b> у <b>{target_name}</b>\nОсталось: <b>×{new_count}</b>", parse_mode="HTML")

    @dp.message(F.text.lower().startswith("обнуление"))
    async def reset_user(message: types.Message):
        if not is_admin(message.from_user.id): return
        parts = message.text.split()
        
        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
        else:
            if len(parts) != 2 or not parts[1].startswith("@"): return await message.reply("❌ обнуление @user")
            target = await db.find_player_by_username(parts[1][1:])
            if not target: return await message.reply("❌ Игрок не найден")
            target_id, target_name = target["user_id"], target["username"]
            
        await db.reset_player(target_id)
        await message.reply(f"✅ Игрок <b>{target_name}</b> обнулён", parse_mode="HTML")