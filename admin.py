
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import (
    change_coins, change_points, set_points, set_level, get_user,
    get_user_ids, bot_stats
)

router = Router()
ADMIN_IDS = {7287316708}
ADMIN_IDS.update(int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit())

def is_admin(uid):
    return uid in ADMIN_IDS

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 آمار کامل", callback_data="adm_stats"),
         InlineKeyboardButton(text="👤 کاربر", callback_data="adm_user")],
        [InlineKeyboardButton(text="🪙 راهنمای تغییر موجودی", callback_data="adm_help"),
         InlineKeyboardButton(text="📣 پیام همگانی", callback_data="adm_broadcast")]
    ])

@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    await message.answer(
        "🛡️ <b>پنل مدیریت</b>\n\n"
        "همه عملیات مدیریتی از همین بخش کنترل می‌شود.\n\n"
        "🪙 سکه: <code>/admin_coins USER_ID AMOUNT</code>\n"
        "🏅 روب پوینت: <code>/admin_points USER_ID AMOUNT</code>\n"
        "⭐ تعیین لول: <code>/admin_level USER_ID LEVEL</code>\n"
        "👤 اطلاعات: <code>/admin_user USER_ID</code>\n"
        "📣 پیام همگانی: <code>/broadcast متن پیام</code>\n\n"
        "مثال منفی برای کم‌کردن: <code>/admin_points 123 -50</code>\n"
        "مدیر می‌تواند حساب خودش را هم تغییر دهد.",
        reply_markup=admin_kb()
    )

@router.callback_query(F.data == "adm_stats")
async def adm_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔ دسترسی نداری.", show_alert=True)
    st = await bot_stats()
    await call.message.answer(
        "📊 <b>آمار ربات</b>\n\n"
        f"👥 کاربران ثبت‌شده: {st['users']:,}\n"
        f"🪙 مجموع سکه‌ها: {st['coins']:,}\n"
        f"🏅 مجموع روب پوینت: {st['points']:,}\n"
        f"⭐ بالاترین لول: {st['max_level']:,}\n"
        f"🖼 مالکیت قاب‌ها: {st['frame_ownerships']:,}\n"
        f"🧊 مجموع آیتم‌های موجودی: {st['inventory_items']:,}\n"
        f"🏅 رکوردهای ماموریت: {st['missions']:,}",
        reply_markup=admin_kb()
    )
    await call.answer()

@router.callback_query(F.data == "adm_help")
async def adm_help(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔ دسترسی نداری.", show_alert=True)
    await call.message.answer(
        "🛠️ <b>عملیات مدیریت</b>\n\n"
        "➕/➖ سکه: <code>/admin_coins ID مقدار</code>\n"
        "➕/➖ روب پوینت: <code>/admin_points ID مقدار</code>\n"
        "⭐ تغییر مستقیم لول: <code>/admin_level ID LEVEL</code>\n"
        "⚠️ مقدار منفی برای کم‌کردن است.",
        reply_markup=admin_kb()
    )
    await call.answer()

@router.callback_query(F.data.in_({"adm_user", "adm_broadcast"}))
async def adm_action_hint(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔ دسترسی نداری.", show_alert=True)
    text = (
        "👤 برای اطلاعات: <code>/admin_user USER_ID</code>"
        if call.data == "adm_user"
        else "📣 برای ارسال پیام به همه: <code>/broadcast متن پیام</code>"
    )
    await call.message.answer(text, reply_markup=admin_kb())
    await call.answer()

@router.message(F.text.startswith("/admin_coins "))
async def admin_coins(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    try:
        _, uid, amount = message.text.split()
        uid, amount = int(uid), int(amount)
        if not await get_user(uid):
            return await message.answer("❌ کاربر پیدا نشد.")
        await change_coins(uid, amount)
        await message.answer(f"✅ {amount:+,} سکه برای {uid} اعمال شد.")
    except Exception:
        await message.answer("قالب: /admin_coins USER_ID AMOUNT")

# Backward-compatible old command.
@router.message(F.text.startswith("/admin_add "))
async def admin_add(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    try:
        _, uid, amount = message.text.split()
        uid, amount = int(uid), int(amount)
        if not await get_user(uid):
            return await message.answer("❌ کاربر پیدا نشد.")
        await change_coins(uid, amount)
        await message.answer(f"✅ {amount:+,} سکه برای {uid} اعمال شد.")
    except Exception:
        await message.answer("قالب: /admin_add USER_ID AMOUNT")

@router.message(F.text.startswith("/admin_points "))
async def admin_points(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    try:
        _, uid, amount = message.text.split()
        uid, amount = int(uid), int(amount)
        u = await get_user(uid)
        if not u:
            return await message.answer("❌ کاربر پیدا نشد.")
        new_value = max(0, u["points"] + amount)
        await set_points(uid, new_value)
        await message.answer(f"✅ روب پوینت کاربر {uid}: {u['points']:,} → {new_value:,}")
    except Exception:
        await message.answer("قالب: /admin_points USER_ID AMOUNT")

@router.message(F.text.startswith("/admin_level "))
async def admin_level(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    try:
        _, uid, level = message.text.split()
        uid, level = int(uid), int(level)
        if level < 1:
            raise ValueError
        u = await get_user(uid)
        if not u:
            return await message.answer("❌ کاربر پیدا نشد.")
        await set_level(uid, level)
        await message.answer(f"✅ لول کاربر {uid}: {u['level']} → {level}")
    except Exception:
        await message.answer("قالب: /admin_level USER_ID LEVEL")

@router.message(F.text.startswith("/admin_user "))
async def admin_user(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    try:
        uid = int(message.text.split()[1])
        u = await get_user(uid)
        if not u:
            return await message.answer("❌ کاربر پیدا نشد.")
        await message.answer(
            f"👤 {u['first_name'] or '-'}\n🆔 {u['user_id']}\n"
            f"🪙 سکه: {u['coins']:,}\n🏅 روب پوینت: {u['points']:,}\n"
            f"⭐ سطح: {u['level']}\n✨ XP: {u['xp']:,}\n❤️ جان: {u['hearts']}"
        )
    except Exception:
        await message.answer("قالب: /admin_user USER_ID")

@router.message(F.text.startswith("/broadcast "))
async def broadcast(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    text = message.text[len("/broadcast "):].strip()
    if not text:
        return await message.answer("متن پیام خالی است.")
    ids = await get_user_ids()
    sent = failed = 0
    bot = message.bot
    for uid in ids:
        try:
            # Direct send: ReplyingBot only adds reply-to when chat matches
            # the current admin chat, so broadcasts never reply in other chats.
            await bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1
    await message.answer(f"📣 پیام همگانی انجام شد.\n✅ ارسال: {sent:,}\n❌ ناموفق: {failed:,}")

@router.message(F.text == "/admin_me")
async def admin_me(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    u = await get_user(message.from_user.id)
    await message.answer(
        f"🛡️ حساب مدیر\n🪙 سکه: {u['coins']:,}\n🏅 روب پوینت: {u['points']:,}\n⭐ لول: {u['level']}"
    )
