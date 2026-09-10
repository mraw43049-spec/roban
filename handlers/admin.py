import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import change_coins, set_points, set_level, get_user, get_user_ids, bot_stats

router = Router()
ADMIN_IDS = {7287316708}
ADMIN_IDS.update(int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit())
admin_sessions = {}

def is_admin(uid):
    return uid in ADMIN_IDS

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 آمار کامل", callback_data="adm_stats")],
        [InlineKeyboardButton(text="👤 مدیریت کاربر", callback_data="adm_user")],
        [InlineKeyboardButton(text="🪙 تغییر سکه", callback_data="adm_coins")],
        [InlineKeyboardButton(text="🏅 تغییر روب‌پوینت", callback_data="adm_points")],
        [InlineKeyboardButton(text="⭐ تغییر لول", callback_data="adm_level")],
        [InlineKeyboardButton(text="📣 پیام همگانی", callback_data="adm_broadcast")],
    ])

def user_actions(uid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪙 تغییر سکه", callback_data=f"adm_uc:{uid}:coins"),
         InlineKeyboardButton(text="🏅 تغییر روب‌پوینت", callback_data=f"adm_uc:{uid}:points")],
        [InlineKeyboardButton(text="⭐ تغییر لول", callback_data=f"adm_uc:{uid}:level")],
        [InlineKeyboardButton(text="🔙 پنل مدیریت", callback_data="adm_home")],
    ])

def parse_int(s):
    table=str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return int(str(s).translate(table).replace(",", "").replace("٬", "").strip())

async def show_panel(target):
    await target.answer(
        "🛡️ <b>پنل مدیریت</b>\n\n"
        "از دکمه‌های زیر برای مدیریت کامل ربات استفاده کن.",
        reply_markup=admin_kb()
    )

@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ شما دسترسی مدیریت ندارید.")
    admin_sessions.pop(message.from_user.id, None)
    await show_panel(message)

@router.callback_query(F.data == "adm_home")
async def adm_home(call: CallbackQuery):
    if not is_admin(call.from_user.id): return await call.answer("⛔ دسترسی ندارید.", show_alert=True)
    admin_sessions.pop(call.from_user.id, None)
    await call.message.edit_text("🛡️ <b>پنل مدیریت</b>\n\nاز دکمه‌های زیر برای مدیریت کامل ربات استفاده کن.", reply_markup=admin_kb())
    await call.answer()

@router.callback_query(F.data == "adm_stats")
async def adm_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id): return await call.answer("⛔ دسترسی ندارید.", show_alert=True)
    st=await bot_stats()
    await call.message.edit_text(
        "📊 <b>آمار کامل ربات</b>\n\n"
        f"👥 کاربران: {st['users']:,}\n"
        f"🪙 مجموع سکه‌ها: {st['coins']:,}\n"
        f"🏅 مجموع روب‌پوینت: {st['points']:,}\n"
        f"⭐ بالاترین لول: {st['max_level']:,}\n"
        f"🖼 مالکیت قاب‌ها: {st['frame_ownerships']:,}\n"
        f"🎒 آیتم‌های موجودی: {st['inventory_items']:,}\n"
        f"🎯 رکوردهای مأموریت: {st['missions']:,}", reply_markup=admin_kb())
    await call.answer()

@router.callback_query(F.data == "adm_user")
async def adm_user_start(call: CallbackQuery):
    if not is_admin(call.from_user.id): return await call.answer("⛔ دسترسی ندارید.", show_alert=True)
    admin_sessions[call.from_user.id]="user"
    await call.message.answer("👤 <b>مدیریت کاربر</b>\n\nشناسه عددی کاربر را بفرست:")
    await call.answer()

@router.callback_query(F.data.in_({"adm_coins","adm_points","adm_level"}))
async def adm_value_start(call: CallbackQuery):
    if not is_admin(call.from_user.id): return await call.answer("⛔ دسترسی ندارید.", show_alert=True)
    kind={"adm_coins":"coins","adm_points":"points","adm_level":"level"}[call.data]
    admin_sessions[call.from_user.id]=kind
    labels={"coins":"🪙 سکه","points":"🏅 روب‌پوینت","level":"⭐ لول"}
    await call.message.answer(f"{labels[kind]}\n\nشناسه کاربر و مقدار را در یک پیام بفرست.\nمثال: <b>123456789 500</b>\nبرای کم‌کردن مقدار منفی بنویس.")
    await call.answer()

@router.callback_query(F.data == "adm_broadcast")
async def adm_broadcast_start(call: CallbackQuery):
    if not is_admin(call.from_user.id): return await call.answer("⛔ دسترسی ندارید.", show_alert=True)
    admin_sessions[call.from_user.id]="broadcast"
    await call.message.answer("📣 <b>پیام همگانی</b>\n\nمتن پیام را بفرست تا برای کاربران ثبت‌شده ارسال شود.")
    await call.answer()

@router.callback_query(F.data.startswith("adm_uc:"))
async def adm_user_action(call: CallbackQuery):
    if not is_admin(call.from_user.id): return await call.answer("⛔ دسترسی ندارید.", show_alert=True)
    _,uid,kind=call.data.split(":")
    uid=int(uid)
    if not await get_user(uid): return await call.answer("❌ کاربر پیدا نشد.", show_alert=True)
    admin_sessions[call.from_user.id]=kind+":"+str(uid)
    labels={"coins":"🪙 مقدار تغییر سکه","points":"🏅 مقدار تغییر روب‌پوینت","level":"⭐ لول جدید"}
    await call.message.answer(f"{labels[kind]} را بفرست.\nمثلاً <b>500</b> یا برای کم‌کردن <b>-500</b>.")
    await call.answer()

@router.message(F.text)
async def admin_input(message: Message):
    uid=message.from_user.id
    if not is_admin(uid) or uid not in admin_sessions: return
    session=admin_sessions.pop(uid)
    if session=="broadcast":
        ids=await get_user_ids(); sent=failed=0
        for target_id in ids:
            try:
                await message.bot.send_message(target_id, message.text)
                sent+=1
            except Exception:
                failed+=1
        return await message.answer(f"📣 <b>پیام همگانی انجام شد.</b>\n\n✅ ارسال موفق: {sent:,}\n❌ ناموفق: {failed:,}", reply_markup=admin_kb())
    if session=="user":
        try: target_id=parse_int(message.text)
        except Exception: return await message.answer("❌ شناسه کاربر باید عدد باشد.")
        u=await get_user(target_id)
        if not u: return await message.answer("❌ این کاربر در ربات ثبت نشده است.", reply_markup=admin_kb())
        return await message.answer(
            f"👤 <b>{u['first_name'] or 'بدون نام'}</b>\n🆔 {u['user_id']}\n🪙 سکه: {u['coins']:,}\n🏅 روب‌پوینت: {u['points']:,}\n⭐ لول: {u['level']}\n✨ XP: {u['xp']:,}\n❤️ جان: {u['hearts']}", reply_markup=user_actions(target_id))
    try:
        parts=message.text.split()
        if len(parts)==2 and session in {"coins","points","level"}:
            target_id=parse_int(parts[0]); amount=parse_int(parts[1])
        elif session.startswith(("coins:","points:","level:")):
            kind,target= session.split(":",1); target_id=int(target); amount=parse_int(message.text)
        else: raise ValueError
        u=await get_user(target_id)
        if not u: return await message.answer("❌ کاربر پیدا نشد.", reply_markup=admin_kb())
        if session in {"level"} or session.startswith("level:"):
            if amount<1: raise ValueError
            await set_level(target_id, amount); result=f"⭐ لول: {u['level']} ← {amount}"
        elif session in {"coins"} or session.startswith("coins:"):
            await change_coins(target_id, amount); result=f"🪙 سکه: {u['coins']:,} ← {u['coins']+amount:,}"
        else:
            new=max(0,u['points']+amount); await set_points(target_id,new); result=f"🏅 روب‌پوینت: {u['points']:,} ← {new:,}"
        await message.answer(f"✅ تغییر با موفقیت انجام شد.\n{result}", reply_markup=admin_kb())
    except Exception:
        await message.answer("❌ اطلاعات واردشده صحیح نیست.", reply_markup=admin_kb())
