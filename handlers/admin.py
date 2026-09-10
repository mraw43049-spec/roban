
import os
import asyncio
from aiogram import Router, F
from aiogram.types import Message
from db import (
    change_coins, change_points, get_user,
    admin_set_level, get_all_user_ids, get_bot_stats
)

router = Router()

SUPER_ADMIN_ID = 7287316708
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}
ADMIN_IDS.add(SUPER_ADMIN_ID)


def admin(uid):
    return uid in ADMIN_IDS


@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    if not admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    await message.answer(
        "🛡️ <b>پنل مدیریت</b>\n\n"
        "🏅 <code>/admin_points USER_ID AMOUNT</code> — افزودن/کسر روب پوینت (منفی هم میشه، حتی برای خودت)\n"
        "⭐ <code>/admin_level USER_ID AMOUNT</code> — افزودن/کسر لول (منفی هم میشه، حتی برای خودت)\n"
        "🪙 <code>/admin_add USER_ID AMOUNT</code> — افزودن/کسر سکه\n"
        "👤 <code>/admin_user USER_ID</code> — مشاهده اطلاعات کامل کاربر\n"
        "📊 <code>/admin_stats</code> — آمار کلی ربات\n"
        "📢 <code>/broadcast متن پیام</code> — ارسال پیام همگانی به همه کاربرا"
    )


@router.message(F.text.startswith("/admin_points "))
async def admin_points(message: Message):
    if not admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    try:
        _, uid, amount = message.text.split()
        uid = int(uid)
        amount = int(amount)
        u = await get_user(uid)
        if not u:
            return await message.answer("❌ کاربر پیدا نشد.")
        await change_points(uid, amount)
        u2 = await get_user(uid)
        await message.answer(f"✅ {amount:+,} روب پوینت برای {uid} ثبت شد.\n🏅 موجودی جدید: {u2['points']:,}")
    except Exception:
        await message.answer("قالب درست:\n/admin_points USER_ID AMOUNT")


@router.message(F.text.startswith("/admin_level "))
async def admin_level(message: Message):
    if not admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    try:
        _, uid, amount = message.text.split()
        uid = int(uid)
        amount = int(amount)
        u = await get_user(uid)
        if not u:
            return await message.answer("❌ کاربر پیدا نشد.")
        new_level = await admin_set_level(uid, amount)
        await message.answer(f"✅ لول کاربر {uid} به {new_level} تغییر کرد.")
    except Exception:
        await message.answer("قالب درست:\n/admin_level USER_ID AMOUNT")


@router.message(F.text.startswith("/admin_add "))
async def admin_add(message: Message):
    if not admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    try:
        _, uid, amount = message.text.split()
        uid = int(uid)
        amount = int(amount)
        await change_coins(uid, amount)
        await message.answer(f"✅ {amount:+,} سکه برای {uid} ثبت شد.")
    except Exception:
        await message.answer("قالب درست:\n/admin_add USER_ID AMOUNT")


@router.message(F.text.startswith("/admin_user "))
async def admin_user(message: Message):
    if not admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    try:
        uid = int(message.text.split()[1])
        u = await get_user(uid)
        if not u:
            return await message.answer("❌ کاربر پیدا نشد.")
        await message.answer(
            f"👤 {u['first_name']}\n🆔 {u['user_id']}\n"
            f"🪙 سکه: {u['coins']:,}\n⭐ لول: {u['level']}\n✨ XP: {u['xp']:,}\n"
            f"🏅 روب پوینت: {u['points']:,}"
        )
    except Exception:
        await message.answer("قالب درست:\n/admin_user USER_ID")


@router.message(F.text == "/admin_me")
async def admin_me(message: Message):
    if not admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    u = await get_user(message.from_user.id)
    await message.answer(
        f"🛡️ حساب مدیر\n🪙 سکه: {u['coins']:,}\n⭐ لول: {u['level']}\n🏅 روب پوینت: {u['points']:,}"
    )


@router.message(F.text == "/admin_stats")
async def admin_stats(message: Message):
    if not admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    s = await get_bot_stats()
    await message.answer(
        "📊 <b>آمار کلی ربات</b>\n\n"
        f"👥 تعداد کاربرا: {s['cnt']:,}\n"
        f"🪙 مجموع سکه‌های همه: {s['coins']:,}\n"
        f"🏅 مجموع روب پوینت‌های همه: {s['points']:,}\n"
        f"✨ مجموع XP همه: {s['xp']:,}\n"
        f"⭐ میانگین لول: {s['avg_level']:.1f}\n"
        f"🏆 بالاترین لول: {s['max_level']}"
    )


@router.message(F.text.startswith("/broadcast"))
async def broadcast(message: Message):
    if not admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    text = message.text[len("/broadcast"):].strip()
    if not text:
        return await message.answer("قالب درست:\n/broadcast متن پیام")

    ids = await get_all_user_ids()
    status = await message.answer(f"📢 در حال ارسال به {len(ids)} کاربر...")
    sent, failed = 0, 0
    for uid in ids:
        try:
            await message.bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await status.edit_text(f"📢 پیام همگانی ارسال شد.\n✅ موفق: {sent}\n❌ ناموفق: {failed}")
