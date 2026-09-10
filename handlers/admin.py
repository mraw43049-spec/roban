from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.event.bases import SkipHandler
from db import change_coins, set_points, set_level, get_user, ensure_user_id, get_user_ids, bot_stats
from config import ADMIN_IDS

router = Router()
admin_sessions = {}


def is_admin(uid: int) -> bool:
    return int(uid) in ADMIN_IDS


def parse_int(value: str) -> int:
    table = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return int(str(value).translate(table).replace(",", "").replace("٬", "").strip())


def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 آمار کامل", callback_data="adm_stats")],
        [InlineKeyboardButton(text="👤 مدیریت کاربر", callback_data="adm_user")],
        [InlineKeyboardButton(text="🪙 تغییر سکه", callback_data="adm_coins")],
        [InlineKeyboardButton(text="🏅 تغییر روب‌پوینت", callback_data="adm_points")],
        [InlineKeyboardButton(text="⭐ تغییر لول", callback_data="adm_level")],
        [InlineKeyboardButton(text="📣 پیام همگانی", callback_data="adm_broadcast")],
    ])


def user_kb(uid: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪙 سکه", callback_data=f"adm_uc:{uid}:coins"),
         InlineKeyboardButton(text="🏅 روب‌پوینت", callback_data=f"adm_uc:{uid}:points")],
        [InlineKeyboardButton(text="⭐ لول", callback_data=f"adm_uc:{uid}:level")],
        [InlineKeyboardButton(text="🔙 پنل مدیریت", callback_data="adm_home")],
    ])


async def show_panel(target):
    await target.answer(
        "🛡️ <b>پنل مدیریت</b>\n\n"
        "از گزینه‌های زیر استفاده کن:",
        reply_markup=admin_kb(),
    )


# The project contains a generic F.text handler in fox_ruby.py. Because that
# router is included before this router, it would swallow /admin and admin
# input messages. Replace only that generic handler with a transparent wrapper
# that skips admin messages so this router can receive them.
def _free_admin_messages_from_fox_router():
    try:
        from handlers import fox_ruby
        old = None
        kept = []
        for h in fox_ruby.router.message.handlers:
            cb = getattr(h, "callback", None)
            if getattr(cb, "__name__", "") == "fox_name_input":
                old = cb
            else:
                kept.append(h)
        if old is None:
            return
        fox_ruby.router.message.handlers[:] = kept

        @fox_ruby.router.message(F.text)
        async def _fox_name_input_bridge(message: Message):
            if is_admin(message.from_user.id) and admin_sessions.get(message.from_user.id):
                raise SkipHandler
            await old(message)
    except Exception:
        # Never prevent the bot from starting if aiogram internals change.
        pass


_free_admin_messages_from_fox_router()


@router.message(F.text.in_({"/admin", "/panel", "/management", "مدیریت"}))
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
    await call.message.edit_text("🛡️ <b>پنل مدیریت</b>\n\nاز گزینه‌های زیر استفاده کن:", reply_markup=admin_kb())
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
        f"🦊 مجموع هوهو: {st['hoohoo']:,}\n"
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
    await call.message.answer("👤 <b>مدیریت کاربر</b>\n\nآیدی عددی کاربر را بفرست:\nمثال: <code>123456789</code>\n⏱️ فرصت: ۶۰ ثانیه")
    await call.answer()


@router.callback_query(F.data.in_({"adm_coins", "adm_points", "adm_level"}))
async def adm_value_start(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔ دسترسی ندارید.", show_alert=True)
    kind = {"adm_coins": "coins", "adm_points": "points", "adm_level": "level"}[call.data]
    admin_sessions[call.from_user.id] = kind
    labels = {"coins": "🪙 سکه", "points": "🏅 روب‌پوینت", "level": "⭐ لول"}
    example = "123456789 500" if kind != "level" else "123456789 5"
    await call.message.answer(
        f"{labels[kind]}\n\nآیدی عددی و مقدار را در یک پیام بفرست.\n"
        f"مثال: <code>{example}</code>\n"
        "برای سکه و روب‌پوینت، عدد منفی یعنی کم‌کردن.\n"
        "⏱️ فرصت: ۶۰ ثانیه"
    )
    await call.answer()


@router.callback_query(F.data == "adm_broadcast")
async def adm_broadcast_start(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔ دسترسی ندارید.", show_alert=True)
    admin_sessions[call.from_user.id] = "broadcast"
    await call.message.answer("📣 <b>پیام همگانی</b>\n\nمتن پیام را بفرست:\n⏱️ فرصت: ۶۰ ثانیه")
    await call.answer()


@router.callback_query(F.data.startswith("adm_uc:"))
async def adm_user_action(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔ دسترسی ندارید.", show_alert=True)
    _, uid_text, kind = call.data.split(":", 2)
    target_id = parse_int(uid_text)
    await ensure_user_id(target_id)
    admin_sessions[call.from_user.id] = f"{kind}:{target_id}"
    labels = {"coins": "🪙 تغییر سکه", "points": "🏅 تغییر روب‌پوینت", "level": "⭐ تغییر لول"}
    await call.message.answer(f"{labels[kind]}\n\nمقدار جدید/تغییر را بفرست.\nبرای سکه و روب‌پوینت مقدار منفی هم می‌توانی بفرستی.\n⏱️ فرصت: ۶۰ ثانیه")
    await call.answer()


@router.message(F.text)
async def admin_input(message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        raise SkipHandler
    session = admin_sessions.get(uid)
    if not session:
        raise SkipHandler

    if session == "broadcast":
        text = (message.text or "").strip()
        admin_sessions.pop(uid, None)
        if not text:
            return await message.answer("❌ متن پیام خالی است.", reply_markup=admin_kb())
        ids = await get_user_ids()
        sent = failed = 0
        for target_id in ids:
            try:
                await message.bot.send_message(target_id, "📣 <b>پیام مدیریت</b>\n\n" + text)
                sent += 1
            except Exception:
                failed += 1
        return await message.answer(f"📣 <b>پیام همگانی انجام شد.</b>\n\n✅ موفق: {sent:,}\n❌ ناموفق: {failed:,}", reply_markup=admin_kb())

    try:
        if session == "user":
            target_id = parse_int(message.text)
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
                f"❤️ جان: {u['hearts']}", reply_markup=user_kb(target_id)
            )

        if session in {"coins", "points", "level"}:
            parts = (message.text or "").split()
            if len(parts) != 2:
                raise ValueError
            target_id = parse_int(parts[0])
            value = parse_int(parts[1])
            kind = session
        else:
            kind, target_text = session.split(":", 1)
            target_id = parse_int(target_text)
            value = parse_int(message.text)

        await ensure_user_id(target_id)
        u = await get_user(target_id)
        old_coins, old_points, old_level = int(u["coins"]), int(u["points"]), int(u["level"])

        if kind == "level":
            if value < 1 or value > 1000:
                raise ValueError
            await set_level(target_id, value)
            new_value = value
            result = f"⭐ لول: {old_level} ← {new_value}"
            notice = f"🔔 <b>تغییر حساب کاربری</b>\n\nمدیریت سطح شما را تغییر داد.\n⭐ لول: {old_level} ← {new_value}"
        elif kind == "coins":
            new_value = max(0, old_coins + value)
            await change_coins(target_id, new_value - old_coins)
            result = f"🪙 سکه: {old_coins:,} ← {new_value:,}"
            notice = f"🔔 <b>تغییر حساب کاربری</b>\n\nمدیریت موجودی سکه شما را تغییر داد.\n🪙 سکه: {old_coins:,} ← {new_value:,}"
        elif kind == "points":
            new_value = max(0, old_points + value)
            await set_points(target_id, new_value)
            result = f"🏅 روب‌پوینت: {old_points:,} ← {new_value:,}"
            notice = f"🔔 <b>تغییر حساب کاربری</b>\n\nمدیریت موجودی روب‌پوینت شما را تغییر داد.\n🏅 روب‌پوینت: {old_points:,} ← {new_value:,}"
        else:
            raise ValueError

        admin_sessions.pop(uid, None)
        try:
            await message.bot.send_message(target_id, notice)
        except Exception:
            pass
        await message.answer("✅ تغییر با موفقیت انجام شد.\n" + result, reply_markup=admin_kb())
    except (ValueError, TypeError):
        await message.answer("❌ مقدار اشتباه است.\nمثال درست: <code>123456789 500</code>")
    except Exception as exc:
        await message.answer(f"❌ عملیات انجام نشد.\n<code>{type(exc).__name__}</code>")
