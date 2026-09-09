
import time
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from db import (
    get_user, change_points, update_xp,
    register_hoohoo, set_hunt_time, level_up_to_next, add_inventory_item
)
from keyboards import back_menu, catch_kb

router = Router()

# --- هوهو: دریافت روب پوینت ---
HOOHOO_KEYS = {"هورهور", "هوهو"}
HOOHOO_COOLDOWN = 180            # 3 دقیقه
HOOHOO_MIN_REWARD = 2
HOOHOO_MAX_REWARD = 5
LEVEL_UP_EVERY = 5               # هر ۵ هوهو یک لول
LEVEL_UP_BONUS_POINTS = 20

# --- شکار ---
HUNT_KEY = "شکار"
HUNT_COOLDOWN = 900              # 15 دقیقه
HUNT_MIN_LEVEL = 2
HUNT_SELL_PER_FOOD = 4           # روب پوینت به ازای هر واحد ارزش غذایی
FOX_XP_PER_FOOD = 5
CATCH_EXPIRE = 300               # 5 دقیقه فرصت برای تصمیم‌گیری

ANIMALS = [
    {"name": "خرگوش", "emoji": "🐇", "food": 2},
    {"name": "موش",   "emoji": "🐭", "food": 2},
    {"name": "راکن",  "emoji": "🦡", "food": 2},
    {"name": "جوجه",  "emoji": "🐤", "food": 1},
    {"name": "اردک",  "emoji": "🦆", "food": 1},
]

pending_catches = {}


def _norm(text):
    return (text or "").strip().replace(" ", "").replace("\u200c", "")


def _fmt_remain(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60} دقیقه و {seconds % 60} ثانیه"


async def hoohoo_action(target, uid):
    u = await get_user(uid)
    now = int(time.time())
    remain = HOOHOO_COOLDOWN - (now - (u["last_hoohoo"] or 0))
    if remain > 0:
        await target.answer(
            f"🦊 هنوز زوده! برای هوهوی بعدی {_fmt_remain(remain)} صبر کن.",
            reply_markup=back_menu()
        )
        return

    reward = random.randint(HOOHOO_MIN_REWARD, HOOHOO_MAX_REWARD)
    await change_points(uid, reward)
    count = await register_hoohoo(uid, now)

    text = f"🦊 هوهو! 🏅 +{reward} روب پوینت گرفتی.\n📊 مجموع هوهوها: {count}"

    if count % LEVEL_UP_EVERY == 0:
        new_level = await level_up_to_next(uid)
        await change_points(uid, LEVEL_UP_BONUS_POINTS)
        text += (
            f"\n\n🎉🎉 تبریک میگم! به لول {new_level} رسیدی!\n"
            f"🎁 جایزه ارتقای سطح: +{LEVEL_UP_BONUS_POINTS} روب پوینت"
        )

    await target.answer(text, reply_markup=back_menu())


@router.message(F.text.func(lambda t: _norm(t) in HOOHOO_KEYS))
async def hoohoo_message(message: Message):
    await hoohoo_action(message, message.from_user.id)


@router.callback_query(F.data == "hoohoo")
async def hoohoo_button(call: CallbackQuery):
    await hoohoo_action(call.message, call.from_user.id)
    await call.answer()


async def hunt_action(target, uid):
    u = await get_user(uid)
    if u["level"] < HUNT_MIN_LEVEL:
        await target.answer(
            f"🔒 شکار از لول {HUNT_MIN_LEVEL} به بعد باز میشه. اول لولت رو با هوهو بالا ببر 🦊",
            reply_markup=back_menu()
        )
        return

    now = int(time.time())
    remain = HUNT_COOLDOWN - (now - (u["last_hunt"] or 0))
    if remain > 0:
        await target.answer(
            f"🏹 هنوز زوده! برای شکار بعدی {_fmt_remain(remain)} صبر کن.",
            reply_markup=back_menu()
        )
        return

    animal = random.choice(ANIMALS)
    await set_hunt_time(uid, now)
    pending_catches[uid] = {**animal, "ts": now}

    await target.answer(
        f"🏹 شکار موفق!\n\n{animal['emoji']} {animal['name']} گیرت اومد.\n"
        f"🍗 ارزش غذایی: {animal['food']}\n\n"
        "می‌خوای باهاش چیکار کنی؟",
        reply_markup=catch_kb()
    )


@router.message(F.text.func(lambda t: _norm(t) == HUNT_KEY))
async def hunt_message(message: Message):
    await hunt_action(message, message.from_user.id)


@router.callback_query(F.data == "hunt")
async def hunt_button(call: CallbackQuery):
    await hunt_action(call.message, call.from_user.id)
    await call.answer()


@router.callback_query(F.data.startswith("catch:"))
async def catch_decision(call: CallbackQuery):
    uid = call.from_user.id
    action = call.data.split(":")[1]
    animal = pending_catches.get(uid)

    if not animal or int(time.time()) - animal["ts"] > CATCH_EXPIRE:
        pending_catches.pop(uid, None)
        await call.message.answer("⌛ زمان تصمیم‌گیری برای این شکار تموم شده.", reply_markup=back_menu())
        await call.answer()
        return

    pending_catches.pop(uid, None)
    name, emoji, food = animal["name"], animal["emoji"], animal["food"]

    if action == "fridge":
        await add_inventory_item(uid, f"{emoji} {name}", 1)
        text = f"🧊 {emoji} {name} رو گذاشتی تو یخچال روبی."
    elif action == "fox":
        xp = food * FOX_XP_PER_FOOD
        await update_xp(uid, xp)
        text = f"🦊 روباه {emoji} {name} رو با اشتها خورد!\n✨ +{xp} XP"
    elif action == "sell":
        price = food * HUNT_SELL_PER_FOOD
        await change_points(uid, price)
        text = f"💰 {emoji} {name} رو فروختی.\n🏅 +{price} روب پوینت"
    else:
        text = "❌ گزینه نامعتبر."

    await call.message.answer(text, reply_markup=back_menu())
    await call.answer()
