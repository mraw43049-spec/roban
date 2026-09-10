from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import (
    change_coins, set_points, set_level, get_user, ensure_user_id,
    get_user_ids, bot_stats,
)
from config import ADMIN_IDS

router = Router()
admin_sessions = {}


def is_admin(uid: int) -> bool:
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


def user_actions(uid: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪙 تغییر سکه", callback_data=f"adm_uc:{uid}:coins"),
         InlineKeyboardButton(text="🏅 تغییر روب‌پوینت", callback_data=f"adm_uc:{uid}:points")],
        [InlineKeyboardButton(text="⭐ تغییر لول", callback_data=f"adm_uc:{uid}:level")],
        [InlineKeyboardButton(text="🔙 پنل مدیریت", callback_data="adm_home")],
    ])


def parse_int(value):
    table = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return int(str(value).translate(table).replace(",", "").replace("٬", "").strip())


async def show_panel(target):
    await target.answer(
        "🛡️ <b>پنل مدیریت</b>\n\n"
        "همه امکانات مدیریتی از دکمه‌های زیر در دسترس است.",
        reply_markup=admin_kb(),
    )


@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ شما دسترسی مدیریت ندارید.")
    admin_sessions.pop(message.from_user.id, None)
    await show_panel(message)


@router.callback_query(F.data == "adm_home")
async def adm_home(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔ دسترسی ندارید.", show_alert=True)
    admin_sessions.pop(call.from_user.id, None)
    await call.message.edit_text("🛡️ <b>پنل مدیریت</b>\n\nهمه امکانات مدیریتی از دکمه‌های زیر در دسترس است.", reply_markup=admin_kb())
    await call.answer()


@router.callback_query(F.data == "adm_stats")
async def adm_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔ دسترسی ندارید.", show_alert=True)
    st = await bot_stats()
    text = (
        "📊 <b>آمار کامل ربات</b>\n\n"
        f"👥 کاربران: {st['users']:,}\n"
        f"🪙 مجموع سکه‌ها: {st['coins']:,}\n"
        f"🏅 مجموع روب‌پوینت: {st['points']:,}\n"
        f"⭐ بالاترین لول: {st['max_level']:,}\n"
        f"🦊 تعداد هوهو: {st['hoohoo']:,}\n"
        f"🖼 مالکیت قاب‌ها: {st['frame_ownerships']:,}\n"
        f"🖼 قاب‌های فعال: {st['active_frames']:,}\n"
        f"🎒 آیتم‌های موجودی: {st['inventory_items']:,}\n"
        f"🎯 رکوردهای مأموریت: {st['missions']:,}"
    )
    await call.message.edit_text(text, reply_markup=admin_kb())
    await call.answer()


@router.callback_query(F.data == "adm_user")
async def adm_user_start(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔ دسترسی ندارید.", show_alert=True)
    admin_sessions[call.from_user.id] = "user"
    await call.message.answer("👤 <b>مدیریت کاربر</b>\n\nآیدی عددی کاربر را بفرست:")
    await call.answer()


@router.callback_query(F.data.in_({"adm_coins", "adm_points", "adm_level"}))
async def adm_value_start(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔ دسترسی ندارید.", show_alert=True)
    kind = {"adm_coins": "coins", "adm_points": "points", "adm_level": "level"}[call.data]
    admin_sessions[call.from_user.id] = kind
    labels = {"coins": "🪙 سکه", "points": "🏅 روب‌پوینت", "level": "⭐ لول"}
    await call.message.answer(
        f"{labels[kind]}\n\n"
        "آیدی کاربر و مقدار را در یک پیام بفرست.\n"
        "مثال: <b>123456789 500</b>\n"
        "برای کم‌کردن سکه یا روب‌پوینت مقدار منفی بنویس."
    )
    await call.answer()


@router.callback_query(F.data == "adm_broadcast")
async def adm_broadcast_start(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔ دسترسی ندارید.", show_alert=True)
    admin_sessions[call.from_user.id] = "broadcast"
    await call.message.answer("📣 <b>پیام همگانی</b>\n\nمتن پیام را بفرست:")
    await call.answer()


@router.callback_query(F.data.startswith("adm_uc:"))
async def adm_user_action(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔ دسترسی ندارید.", show_alert=True)
    _, uid_text, kind = call.data.split(":", 2)
    uid = int(uid_text)
    await ensure_user_id(uid)
    admin_sessions[call.from_user.id] = f"{kind}:{uid}"
    labels = {"coins": "🪙 مقدار تغییر سکه", "points": "🏅 مقدار تغییر روب‌پوینت", "level": "⭐ لول جدید"}
    await call.message.answer(
        f"{labels[kind]} را بفرست.\n"
        "مثلاً <b>500</b> یا برای کم‌کردن <b>-500</b>."
    )
    await call.answer()


@router.message(F.func(lambda m: m.from_user.id in admin_sessions))
async def admin_input(message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    session = admin_sessions.get(uid)
    if not session:
        return

    if session == "broadcast":
        admin_sessions.pop(uid, None)
        ids = await get_user_ids()
        sent = failed = 0
        for target_id in ids:
            try:
                await message.bot.send_message(target_id, message.text)
                sent += 1
            except Exception:
                failed += 1
        return await message.answer(
            f"📣 <b>پیام همگانی انجام شد.</b>\n\n✅ موفق: {sent:,}\n❌ ناموفق: {failed:,}",
            reply_markup=admin_kb(),
        )

    if session == "user":
        try:
            target_id = parse_int(message.text)
        except Exception:
            return await message.answer("❌ آیدی باید فقط عدد باشد.")
        await ensure_user_id(target_id)
        u = await get_user(target_id)
        admin_sessions.pop(uid, None)
        return await message.answer(
            f"👤 <b>{u['first_name'] or 'کاربر'}</b>\n"
            f"🆔 {u['user_id']}\n"
            f"🪙 سکه: {u['coins']:,}\n"
            f"🏅 روب‌پوینت: {u['points']:,}\n"
            f"⭐ لول: {u['level']}\n"
            f"✨ XP: {u['xp']:,}\n"
            f"❤️ جان: {u['hearts']}",
            reply_markup=user_actions(target_id),
        )

    try:
        if session in {"coins", "points", "level"}:
            parts = message.text.split()
            if len(parts) != 2:
                raise ValueError
            target_id = parse_int(parts[0])
            amount = parse_int(parts[1])
            kind = session
        elif session.startswith(("coins:", "points:", "level:")):
            kind, target_text = session.split(":", 1)
            target_id = int(target_text)
            amount = parse_int(message.text)
        else:
            raise ValueError

        await ensure_user_id(target_id)
        u = await get_user(target_id)
        if kind == "level":
            if amount < 1:
                raise ValueError
            await set_level(target_id, amount)
            result = f"⭐ لول: {u['level']} ← {amount}"
        elif kind == "coins":
            new_value = max(0, u['coins'] + amount)
            await change_coins(target_id, new_value - u['coins'])
            result = f"🪙 سکه: {u['coins']:,} ← {new_value:,}"
        else:
            new_value = max(0, u['points'] + amount)
            await set_points(target_id, new_value)
            result = f"🏅 روب‌پوینت: {u['points']:,} ← {new_value:,}"

        admin_sessions.pop(uid, None)
        # اطلاع‌رسانی مستقیم به کاربر هدف؛ حتی اگر مدیر خودش باشد.
        try:
            if kind == "level":
                notice = f"🔔 <b>تغییر حساب کاربری</b>\n\n⭐ سطح شما توسط مدیریت از {u['level']} به {amount} تغییر کرد."
            elif kind == "coins":
                notice = f"🔔 <b>تغییر حساب کاربری</b>\n\n🪙 موجودی سکه شما توسط مدیریت تغییر کرد.\n{result}"
            else:
                notice = f"🔔 <b>تغییر حساب کاربری</b>\n\n🏅 موجودی روب‌پوینت شما توسط مدیریت تغییر کرد.\n{result}"
            await message.bot.send_message(target_id, notice)
        except Exception:
            pass
        await message.answer("✅ تغییر با موفقیت انجام شد.\n" + result, reply_markup=admin_kb())
    except Exception:
        await message.answer("❌ مقدار واردشده صحیح نیست. دوباره با قالب درست وارد کن.")
