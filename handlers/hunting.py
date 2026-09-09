
import time
import random
import asyncio
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
HOOHOO_BASE_REWARD = 20          # پاداش هوهوی اول
HOOHOO_STEP = 5                  # هر هوهو نسبت به قبلی این‌قدر بیشتر میشه
LEVEL_UP_EVERY = 5               # هر ۵ هوهو یک لول

# پاداش ارتقای لول: لول ۲ = 250، هر لول بالاتر 50 تا بیشتر
LEVEL_UP_BASE_BONUS = 250
LEVEL_UP_BONUS_STEP = 50

# قابلیت‌هایی که با رسیدن به هر لول باز می‌شن (برای پیام تبریک)
LEVEL_UNLOCKS = {
    2: ["🏹 شکار", "🎮 پیوستن به بازی", "📥 دریافت انتقال"],
    3: ["🦊 روباه", "🛠 ساخت بازی", "🔁 انتقال روب پوینت"],
    4: ["🏦 بانک", "🎰 پیوستن به کازینو"],
    5: ["🏗 ساخت کازینو"],
    7: ["🧊 یخچال روبی"],
}

# --- شکار ---
HUNT_KEY = "شکار"
HUNT_COOLDOWN = 900              # 1 دقیقه
HUNT_MIN_LEVEL = 2
HUNT_SELL_PER_FOOD = 4           # روب پوینت به ازای هر واحد ارزش غذایی
FOX_XP_PER_FOOD = 5
CATCH_EXPIRE = 300               # 5 دقیقه فرصت برای تصمیم‌گیری

FRIDGE_UNLOCK_LEVEL = 7
FOX_UNLOCK_LEVEL = 3

ANIMALS = [
    {"name": "خرگوش", "emoji": "🐇", "food": 3},
    {"name": "موش",   "emoji": "🐭", "food": 2},
    {"name": "راکن",  "emoji": "🦡", "food": 2},
    {"name": "جوجه",  "emoji": "🐤", "food": 1},
    {"name": "اردک",  "emoji": "🦆", "food": 1},
]

pending_catches = {}


def _norm(text):
    return (text or "").strip().replace(" ", "").replace("\u200c", "")


def _fmt_mmss(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


def _level_up_bonus(new_level):
    return LEVEL_UP_BASE_BONUS + max(0, (new_level - 2)) * LEVEL_UP_BONUS_STEP


async def hoohoo_action(target, uid):
    u = await get_user(uid)
    now = int(time.time())
    remain = HOOHOO_COOLDOWN - (now - (u["last_hoohoo"] or 0))
    if remain > 0:
        await target.answer(
            f"🦊 هنوز زوده!\n⏳ بعد از {_fmt_mmss(remain)} دیگه میتونی دوباره هو هو کنی"
        )
        return

    count = await register_hoohoo(uid, now)
    reward = HOOHOO_BASE_REWARD + (count - 1) * HOOHOO_STEP
    await change_points(uid, reward)
    u2 = await get_user(uid)

    text = (
        f"🐾 {reward} روب پوینت 🦊 گرفتی\n"
        f"🏆 روب پوینت هات: {u2['points']}\n\n"
        f"⏳ بعد از {_fmt_mmss(HOOHOO_COOLDOWN)} دیگه میتونی دوباره هو هو کنی"
    )

    if count % LEVEL_UP_EVERY == 0:
        new_level = await level_up_to_next(uid)
        bonus = _level_up_bonus(new_level)
        await change_points(uid, bonus)
        text += (
            f"\n\n🎉🎉 تبریک میگم! به لول {new_level} رسیدی!\n"
            f"🎁 جایزه ارتقای سطح: +{bonus} روب پوینت"
        )
        unlocks = LEVEL_UNLOCKS.get(new_level)
        if unlocks:
            text += "\n\n🔓 این قابلیت‌های جدید برات باز شد:\n" + "\n".join(f"┘─ {x}" for x in unlocks)

    await target.answer(text)


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
            f"🏹 هنوز زوده! برای شکار بعدی {_fmt_mmss(remain)} صبر کن.",
            reply_markup=back_menu()
        )
        return

    animal = random.choice(ANIMALS)
    await set_hunt_time(uid, now)
    pending_catches[uid] = {**animal, "ts": now}

    msg = await target.answer("🏹 داری شکار میکنی...")
    for _ in range(3):
        await asyncio.sleep(0.4)
        flash = random.choice(ANIMALS)
        try:
            await msg.edit_text(f"🏹 داری شکار میکنی... {flash['emoji']}")
        except Exception:
            pass
    await asyncio.sleep(0.4)

    try:
        await msg.edit_text(
            f"{animal['emoji']}\n\n"
            f"شما {animal['emoji']} {animal['name']} شکار کردید!\n"
            f"🍗 ارزش غذایی: {animal['food']}\n\n"
            "می‌خوای باهاش چیکار کنی؟",
            reply_markup=catch_kb()
        )
    except Exception:
        await target.answer(
            f"{animal['emoji']}\n\n"
            f"شما {animal['emoji']} {animal['name']} شکار کردید!\n"
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

    name, emoji, food = animal["name"], animal["emoji"], animal["food"]
    u = await get_user(uid)

    if action == "fridge":
        if u["level"] < FRIDGE_UNLOCK_LEVEL:
            await call.answer(f"🔒 یخچال از لول {FRIDGE_UNLOCK_LEVEL} باز میشه.", show_alert=True)
            return
        pending_catches.pop(uid, None)
        await add_inventory_item(uid, f"{emoji} {name}", 1)
        text = f"🧊 {emoji} {name} رو گذاشتی تو یخچال روبی."

    elif action == "fox":
        if u["level"] < FOX_UNLOCK_LEVEL:
            await call.answer(f"🔒 روباه از لول {FOX_UNLOCK_LEVEL} باز میشه.", show_alert=True)
            return
        pending_catches.pop(uid, None)
        xp = food * FOX_XP_PER_FOOD
        await update_xp(uid, xp)
        text = f"🦊 روباه {emoji} {name} رو با اشتها خورد!\n✨ +{xp} XP"

    elif action == "sell":
        pending_catches.pop(uid, None)
        price = food * HUNT_SELL_PER_FOOD
        await change_points(uid, price)
        text = f"💰 {emoji} {name} رو فروختی.\n🏅 +{price} روب پوینت"

    else:
        await call.answer()
        return

    await call.message.answer(text, reply_markup=back_menu())
    await call.answer()
