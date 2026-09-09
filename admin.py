import os
from aiogram import Router, F
from aiogram.types import Message
try:
    from app.db import change_coins
except ModuleNotFoundError:
    from db import change_coins

router=Router()
ADMIN_IDS={int(x) for x in os.getenv("ADMIN_IDS","").split(",") if x.strip().isdigit()}

def admin(uid): return uid in ADMIN_IDS

@router.message(F.text=="/admin")
async def admin_panel(message: Message):
    if not admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    await message.answer("🛡️ پنل مدیریت\n\n/admin_add USER_ID AMOUNT")

@router.message(F.text.startswith("/admin_add "))
async def admin_add(message: Message):
    if not admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مدیریت نداری.")
    try:
        _,uid,amount=message.text.split()
        await change_coins(int(uid),int(amount))
        await message.answer("✅ انجام شد.")
    except Exception:
        await message.answer("قالب: /admin_add USER_ID AMOUNT")
