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

HOOHOO_COOLDOWN = 180
HOOHOO_MIN_REWARD = 2
HOOHOO_MAX_REWARD = 5
LEVEL_UP_EVERY = 5
LEVEL_UP_BONUS_POINTS = 20
HUNT_KEY = "شکار"
HUNT_COOLDOWN = 900
HUNT_MIN_LEVEL = 2
HUNT_SELL_PER_FOOD = 4
FOX_XP_PER_FOOD = 5
CATCH_EXPIRE = 60

LEVEL_UNLOCKS = {
    2: ["🏹 شکار", "🎮 پیوستن به بازی", "📥 دریافت انتقال"],
    3: ["🦊 روباه", "🛠 ساخت بازی", "🔁 انتقال روب پوینت"],
    4: ["🏦 بانک", "🎰 پیوستن به کازینو"],
    5: ["🏗 ساخت کازینو"],
}

ANIMALS = [
    {"name": "خرگوش", "emoji": "🐇", "food": 2},
    {"name": "موش", "emoji": "🐭", "food": 2},
    {"name": "راکن", "emoji": "🦡", "food": 2},
    {"name": "جوجه", "emoji": "🐤", "food": 1},
    {"name": "اردک", "emoji": "🦆", "food": 1},
]

pending_catches = {}
hunt_tasks = {}


def _norm(text):
    return (text or "").strip().replace(" ", "").replace("\u200c", "")


def _fmt_mmss(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


async def hoohoo_action(target, uid):
    u = await get_user(uid)
    if not u:
        return await target.answer("❌ حساب کاربری پیدا نشد. دوباره /start را بزن.")
    now = int(time.time())
    remain = HOOHOO_COOLDOWN - (now - (u["last_hoohoo"] or 0))
    if remain > 0:
        return await target.answer(
            f"🦊 هنوز زوده!\n⏳ {_fmt_mmss(remain)} تا هوهو بعدی باقی مانده.",
            reply_markup=back_menu()
        )

    reward = random.randint(HOOHOO_MIN_REWARD, HOOHOO_MAX_REWARD)

    # یک انیمیشن سبک با همان ایموجی؛ Unicode emoji خودش فایل انیمیشن ندارد.
    animation_msg = await target.answer("🦊")
    for text in ("🦊✨", "🦊💫", "🦊✨✨", "🦊"):
        await asyncio.sleep(0.18)
        try:
            await animation_msg.edit_text(text)
        except Exception:
            break

    await change_points(uid, reward)
    count = await register_hoohoo(uid, now)
    u2 = await get_user(uid)

    text = (
        f"🦊 هوهو انجام شد!\n\n"
        f"🏅 +{reward} روب‌پوینت\n"
        f"🏆 موجودی روب‌پوینت: {u2['points']:,}\n"
        f"🔢 تعداد هوهو: {count:,}\n\n"
        f"⏳ هوهو بعدی: {_fmt_mmss(HOOHOO_COOLDOWN)}"
    )

    if count % LEVEL_UP_EVERY == 0:
        new_level = await level_up_to_next(uid)
        await change_points(uid, LEVEL_UP_BONUS_POINTS)
        text += f"\n\n🎉 تبریک! به لول {new_level} رسیدی!\n🎁 +{LEVEL_UP_BONUS_POINTS} روب‌پوینت"
        unlocks = LEVEL_UNLOCKS.get(new_level)
        if unlocks:
            text += "\n\n🔓 قابلیت‌های جدید:\n" + "\n".join(f"┘─ {item}" for item in unlocks)

    # پاسخ نهایی هم Reply است و هم دکمه‌ها را دارد.
    await target.answer(text, reply_markup=back_menu())


@router.message(F.text.func(lambda t: _norm(t) in {"هورهور", "هوهو"}))
async def hoohoo_message(message: Message):
    await hoohoo_action(message, message.from_user.id)


@router.callback_query(F.data == "hoohoo")
async def hoohoo_button(call: CallbackQuery):
    await hoohoo_action(call.message, call.from_user.id)
    await call.answer()


async def _expire_hunt(uid, msg, created):
    await asyncio.sleep(CATCH_EXPIRE)
    item = pending_catches.get(uid)
    if item and item.get("ts") == created:
        pending_catches.pop(uid, None)
        try:
            await msg.edit_text("⌛ فرصت تصمیم‌گیری این شکار تمام شد.\nبرای شکار بعدی دوباره «شکار» را بفرست.")
        except Exception:
            pass
    hunt_tasks.pop(uid, None)


async def hunt_action(target, uid):
    u = await get_user(uid)
    if not u:
        return await target.answer("❌ حساب کاربری پیدا نشد. دوباره /start را بزن.")
    if u["level"] < HUNT_MIN_LEVEL:
        return await target.answer(
            f"🔒 شکار از لول {HUNT_MIN_LEVEL} باز می‌شود. اول با هوهو لولت را بالا ببر 🦊",
            reply_markup=back_menu()
        )

    now = int(time.time())
    remain = HUNT_COOLDOWN - (now - (u["last_hunt"] or 0))
    if remain > 0:
        return await target.answer(
            f"🏹 هنوز زوده! برای شکار بعدی {_fmt_mmss(remain)} صبر کن.",
            reply_markup=back_menu()
        )

    old_task = hunt_tasks.pop(uid, None)
    if old_task:
        old_task.cancel()

    animal = random.choice(ANIMALS)
    await set_hunt_time(uid, now)
    pending_catches[uid] = {**animal, "ts": now}

    msg = await target.answer(animal["emoji"])
    # انیمیشن سبک با همان ایموجی شکار
    for suffix in ("✨", "💫", "✨✨", ""):
        await asyncio.sleep(0.20)
        try:
            await msg.edit_text(f"{animal['emoji']}{suffix}")
        except Exception:
            break

    try:
        await msg.edit_text(
            f"{animal['emoji']}\n\n"
            f"شما {animal['emoji']} {animal['name']} شکار کردید!\n"
            f"🍗 ارزش غذایی: {animal['food']}\n\n"
            "می‌خوای باهاش چیکار کنی؟",
            reply_markup=catch_kb()
        )
    except Exception:
        msg = await target.answer(
            f"{animal['emoji']}\n\nشما {animal['emoji']} {animal['name']} شکار کردید!\n"
            f"🍗 ارزش غذایی: {animal['food']}\n\nمی‌خوای باهاش چیکار کنی؟",
            reply_markup=catch_kb()
        )

    hunt_tasks[uid] = asyncio.create_task(_expire_hunt(uid, msg, now))


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
    item = pending_catches.get(uid)
    if not item or int(time.time()) - item["ts"] > CATCH_EXPIRE:
        pending_catches.pop(uid, None)
        await call.message.edit_text("⌛ زمان تصمیم‌گیری این شکار تمام شد.\nبرای شکار بعدی دوباره «شکار» را بفرست.")
        await call.answer()
        return

    task = hunt_tasks.pop(uid, None)
    if task:
        task.cancel()
    pending_catches.pop(uid, None)

    action = call.data.split(":", 1)[1]
    name, emoji, food = item["name"], item["emoji"], item["food"]

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
        text = f"💰 {emoji} {name} رو فروختی.\n🏅 +{price} روب‌پوینت"
    else:
        text = "❌ گزینه نامعتبر."

    await call.message.answer(text, reply_markup=back_menu())
    await call.answer()
