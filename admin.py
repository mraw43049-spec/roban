
import os
from aiogram import Router, F
from aiogram.types import Message
from db import change_coins, get_user

router=Router()
ADMIN_IDS={int(x) for x in os.getenv("ADMIN_IDS","").split(",") if x.strip().isdigit()}

def admin(uid): return uid in ADMIN_IDS

@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    if not admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    await message.answer(
        "🛡️ <b>پنل مدیریت</b>\n\n"
        "/admin_add USER_ID AMOUNT — افزودن/کسر سکه\n"
        "/admin_user USER_ID — مشاهده کاربر\n"
        "/admin_me — موجودی حساب مدیر"
    )

@router.message(F.text.startswith("/admin_add "))
async def admin_add(message: Message):
    if not admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    try:
        _,uid,amount=message.text.split()
        uid=int(uid); amount=int(amount)
        await change_coins(uid,amount)
        await message.answer(f"✅ {amount:+,} سکه برای {uid} ثبت شد.")
    except Exception:
        await message.answer("قالب: /admin_add USER_ID AMOUNT")

@router.message(F.text.startswith("/admin_user "))
async def admin_user(message: Message):
    if not admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    try:
        uid=int(message.text.split()[1])
        u=await get_user(uid)
        if not u:
            return await message.answer("❌ کاربر پیدا نشد.")
        await message.answer(
            f"👤 {u['first_name']}\n🆔 {u['user_id']}\n"
            f"🪙 {u['coins']}\n⭐ سطح {u['level']}\n✨ XP {u['xp']}\n🏅 پوینت {u['points']}"
        )
    except Exception:
        await message.answer("قالب: /admin_user USER_ID")

@router.message(F.text == "/admin_me")
async def admin_me(message: Message):
    if not admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    u=await get_user(message.from_user.id)
    await message.answer(f"🛡️ حساب مدیر\n🪙 موجودی: {u['coins']} سکه")
