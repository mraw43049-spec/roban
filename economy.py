import time, random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from db import get_user, set_daily, change_coins, update_xp, transfer
from keyboards import back_menu

router = Router()

@router.message(F.text == "/daily")
async def daily(message: Message):
    u = await get_user(message.from_user.id)
    now = int(time.time())
    if now - u["last_daily"] < 86400:
        remain = 86400 - (now-u["last_daily"])
        await message.answer(f"🔔 جایزه امروز گرفته شده. ⏳ {remain//3600} ساعت و {(remain%3600)//60} دقیقه باقی مانده.", reply_markup=back_menu())
        return
    await set_daily(message.from_user.id, now, 100)
    await update_xp(message.from_user.id, 20)
    await message.answer("🎁 +100 سکه\n✨ +20 XP", reply_markup=back_menu())

@router.message(F.text == "/level")
async def level(message: Message):
    u=await get_user(message.from_user.id)
    await message.answer(f"⭐ سطح {u['level']}\n✨ XP: {u['xp']}\n🎯 تا سطح بعد: {u['level']*100-u['xp']}", reply_markup=back_menu())

@router.message(F.text == "/missions")
async def missions(message: Message):
    await message.answer("🏅 ماموریت‌ها:\n\n🔔 دریافت جایزه روزانه\n🎲 انجام یک بازی\n🦊 باز کردن مارکت", reply_markup=back_menu())

@router.message(F.text == "/market")
async def market(message: Message):
    await message.answer("🦊 <b>مارکت روبی</b>\n\n🪙 اقتصاد مجازی آماده توسعه است.", reply_markup=back_menu())

@router.message(F.text == "/bank")
async def bank(message: Message):
    u=await get_user(message.from_user.id)
    await message.answer(f"💳 <b>بانک</b>\n\nموجودی: {u['coins']} سکه\n\nانتقال: /pay USER_ID AMOUNT", reply_markup=back_menu())

@router.message(F.text.startswith("/pay "))
async def pay(message: Message):
    try:
        _,uid,amount=message.text.split()
        ok=await transfer(message.from_user.id,int(uid),int(amount))
    except Exception:
        ok=False
    await message.answer("✅ انتقال انجام شد." if ok else "❌ انتقال ناموفق بود.")

@router.callback_query(F.data == "daily")
async def daily_button(call: CallbackQuery):
    await call.message.answer("🔔 برای دریافت جایزه از /daily استفاده کن.")
    await call.answer()

@router.callback_query(F.data == "wheel")
async def wheel_button(call: CallbackQuery):
    prize=random.choice([10,20,30,50,75,100])
    await change_coins(call.from_user.id,prize)
    await update_xp(call.from_user.id,10)
    await call.message.answer(f"🔄 چرخ شانس: +{prize} سکه مجازی\n✨ +10 XP", reply_markup=back_menu())
    await call.answer()

@router.message(F.text == "/wheel")
async def wheel_cmd(message: Message):
    prize=random.choice([10,20,30,50,75,100])
    await change_coins(message.from_user.id,prize)
    await update_xp(message.from_user.id,10)
    await message.answer(f"🔄 چرخ شانس: +{prize} سکه مجازی\n✨ +10 XP", reply_markup=back_menu())

@router.callback_query(F.data == "dice")
async def dice_button(call: CallbackQuery):
    n=random.randint(1,6)
    await update_xp(call.from_user.id,5)
    await call.message.answer(f"🎲 تاس: <b>{n}</b>\n✨ +5 XP", reply_markup=back_menu())
    await call.answer()

@router.message(F.text == "/dice")
async def dice_cmd(message: Message):
    n=random.randint(1,6)
    await update_xp(message.from_user.id,5)
    await message.answer(f"🎲 تاس: <b>{n}</b>\n✨ +5 XP", reply_markup=back_menu())

@router.message(F.text == "/raffle")
async def raffle(message: Message):
    await message.answer("👑 رافل تفریحی: بدون پرداخت و جایزه پولی واقعی.", reply_markup=back_menu())

@router.message(F.text == "/factory")
async def factory(message: Message):
    await update_xp(message.from_user.id,10)
    await message.answer("⚡ کارخانه: +10 XP برای فعالیت کارخانه.", reply_markup=back_menu())
