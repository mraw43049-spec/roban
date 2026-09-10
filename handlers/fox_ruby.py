import time
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from db import (
    get_user, get_fox, buy_fox, rename_fox, upgrade_fox,
    withdraw_fox_points, feed_fox, create_ruby_game, list_open_ruby_games,
    join_ruby_game, cancel_ruby_game,
)

router = Router()
fox_name_sessions = {}
FOX_PRICE = 100
FOX_MIN_LEVEL = 3
RUBY_CREATE_MIN_LEVEL = 3
RUBY_JOIN_MIN_LEVEL = 2
RUBY_MAX_STAKE = 500_000


def fox_kb(has_fox=True, can_upgrade=False):
    rows = []
    if has_fox:
        rows.append([
            InlineKeyboardButton(text="✏️ تغییر نام روباه", callback_data="fox_rename"),
            InlineKeyboardButton(text="💰 برداشت روب‌پوینت", callback_data="fox_withdraw"),
        ])
        rows.append([InlineKeyboardButton(text="🍗 اطلاعات روباه", callback_data="fox_refresh")])
        if can_upgrade:
            rows.append([InlineKeyboardButton(text="⬆️ ارتقای روباه", callback_data="fox_upgrade")])
    else:
        rows.append([InlineKeyboardButton(text=f"🦊 خرید روباه — {FOX_PRICE} روب‌پوینت", callback_data="fox_buy")])
    rows.append([InlineKeyboardButton(text="💎 بازی‌های روبی", callback_data="ruby_games")])
    rows.append([InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ruby_games_kb(games, owner_id):
    rows = []
    for g in games:
        rows.append([InlineKeyboardButton(
            text=f"🎮 بازی #{g['id']} — {g['stake']:,} روب‌پوینت",
            callback_data=f"ruby_join:{g['id']}"
        )])
        if g["creator_id"] == owner_id:
            rows.append([InlineKeyboardButton(text=f"❌ لغو بازی #{g['id']}", callback_data=f"ruby_cancel:{g['id']}")])
    rows.append([InlineKeyboardButton(text="🔄 تازه‌سازی", callback_data="ruby_games")])
    rows.append([InlineKeyboardButton(text="🔙 منو", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def parse_number(text):
    table = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return int(str(text).translate(table).replace(",", "").replace("٬", "").strip())


def fox_text(u, f):
    if not f:
        return (
            "🦊 <b>روباه</b>\n\n"
            f"🔒 روباه از لول {FOX_MIN_LEVEL} باز می‌شود.\n"
            f"💰 قیمت خرید: {FOX_PRICE} روب‌پوینت\n\n"
            f"⭐ لول فعلی تو: {u['level']}"
        )
    next_h = max(0, (u["level"] * 5) - u["hoohoo_count"])
    upgrade = "آماده ارتقاست" if f["level"] < u["level"] else "با رسیدن به لول بالاتر باز می‌شود"
    return (
        f"🦊 <b>{f['name']}</b>\n\n"
        f"⭐ سطح روباه: {f['level']}\n"
        f"⭐ سطح تو: {u['level']}\n"
        f"🍗 شکم: {f['hunger']}/100\n"
        f"🏅 روب‌پوینت جمع‌شده توسط روباه: {f['stored_points']:,}\n"
        f"🍖 تعداد غذا دادن: {f['feed_count']:,}\n\n"
        f"🗣️ هوهوهای انجام‌شده: {u['hoohoo_count']:,}\n"
        f"⏳ هوهو تا لول بعد: {next_h:,}\n"
        f"⬆️ وضعیت ارتقا: {upgrade}\n\n"
        "هر غذایی که در شکار به روباه بدهی، شکمش را پر می‌کند و روب‌پوینت برای روباه ذخیره می‌شود."
    )


async def show_fox(target, uid):
    u = await get_user(uid)
    f = await get_fox(uid)
    if u["level"] < FOX_MIN_LEVEL:
        return await target.answer(
            f"🔒 <b>روباه هنوز باز نشده</b>\n\n⭐ برای خرید روباه باید به لول {FOX_MIN_LEVEL} برسی.\n💰 قیمت روباه: {FOX_PRICE} روب‌پوینت\n\nسطح فعلی تو: {u['level']}",
            reply_markup=fox_kb(False)
        )
    await target.answer(fox_text(u, f), reply_markup=fox_kb(bool(f), bool(f and f['level'] < u['level'])))


@router.message(F.text == "روباه")
@router.message(F.text == "/fox")
async def fox_message(message: Message):
    await show_fox(message, message.from_user.id)

@router.callback_query(F.data == "fox")
async def fox_button(call: CallbackQuery):
    await show_fox(call.message, call.from_user.id)
    await call.answer()

@router.callback_query(F.data == "fox_buy")
async def fox_buy(call: CallbackQuery):
    ok, reason = await buy_fox(call.from_user.id, FOX_PRICE)
    messages = {
        "level": "🔒 خرید روباه از لول ۳ باز می‌شود.",
        "points": "❌ ۱۰۰ روب‌پوینت برای خرید روباه لازم داری.",
        "owned": "🦊 تو قبلاً روباه داری.",
    }
    await call.message.answer("✅ روباه با موفقیت خریداری شد!\n\n" + fox_text(await get_user(call.from_user.id), await get_fox(call.from_user.id)) if ok else messages.get(reason, "❌ خرید انجام نشد."), reply_markup=fox_kb(True) if ok else fox_kb(False))
    await call.answer()

@router.callback_query(F.data == "fox_rename")
async def fox_rename_start(call: CallbackQuery):
    if not await get_fox(call.from_user.id):
        return await call.answer("❌ اول روباه را بخر.", show_alert=True)
    fox_name_sessions[call.from_user.id] = int(time.time())
    await call.message.answer("✏️ اسم جدید روباه را بفرست.\nنام باید بین ۲ تا ۲۴ کاراکتر باشد.\n⏱️ فرصت: ۶۰ ثانیه")
    await call.answer()

@router.message(F.text)
async def fox_name_input(message: Message):
    uid = message.from_user.id
    created = fox_name_sessions.get(uid)
    if created is None:
        return
    if int(time.time()) - created > 60:
        fox_name_sessions.pop(uid, None)
        return await message.answer("⌛ زمان تغییر نام تمام شد. دوباره از بخش روباه اقدام کن.")
    # جلوگیری از گرفتن دستورات به‌عنوان اسم
    if message.text.startswith("/") or message.text in {"شکار", "روباه"}:
        return
    name = message.text.strip()
    if not await rename_fox(uid, name):
        return await message.answer("❌ نام باید بین ۲ تا ۲۴ کاراکتر باشد. دوباره بفرست.")
    fox_name_sessions.pop(uid, None)
    await message.answer(f"✅ اسم روباه به «{name}» تغییر کرد.", reply_markup=fox_kb(True))

@router.callback_query(F.data == "fox_refresh")
async def fox_refresh(call: CallbackQuery):
    await show_fox(call.message, call.from_user.id)
    await call.answer()

@router.callback_query(F.data == "fox_upgrade")
async def fox_upgrade(call: CallbackQuery):
    ok, reason, level = await upgrade_fox(call.from_user.id)
    if ok:
        await call.message.answer(f"🎉 روباه به سطح {level} ارتقا پیدا کرد!", reply_markup=fox_kb(True, False))
    elif reason == "locked":
        await call.message.answer("🔒 برای ارتقای بیشتر باید اول سطح کاربری خودت بالاتر برود.", reply_markup=fox_kb(True, False))
    elif reason == "points":
        await call.message.answer(f"❌ روب‌پوینت کافی نیست. هزینه این ارتقا: {50 * level:,} روب‌پوینت.", reply_markup=fox_kb(True, True))
    else:
        await call.message.answer("❌ روباه پیدا نشد.", reply_markup=fox_kb(False))
    await call.answer()

@router.callback_query(F.data == "fox_withdraw")
async def fox_withdraw(call: CallbackQuery):
    amount = await withdraw_fox_points(call.from_user.id)
    await call.message.answer(f"💰 {amount:,} روب‌پوینت از روباه برداشت شد و به موجودی تو اضافه شد." if amount else "❌ روباه هنوز روب‌پوینتی جمع نکرده است.", reply_markup=fox_kb(True))
    await call.answer()

# ---------- بازی‌های روبی ----------
async def show_ruby_games(target, uid):
    u = await get_user(uid)
    games = await list_open_ruby_games()
    text = (
        "💎 <b>بازی‌های روبی</b>\n\n"
        f"⭐ لول تو: {u['level']}\n"
        "🔓 پیوستن: از لول ۲\n"
        "🔓 ساخت بازی: از لول ۳\n"
        f"📌 سقف مبلغ: {RUBY_MAX_STAKE:,} روب‌پوینت\n\n"
    )
    if games:
        text += "بازی‌های فعال:\n" + "\n".join(f"🎮 #{g['id']} — {g['stake']:,} روب‌پوینت" for g in games)
    else:
        text += "فعلاً بازی فعالی وجود ندارد.\n\nبرای ساخت بازی بنویس:\n<code>ساخت بازی روبی 100</code>"
    await target.answer(text, reply_markup=ruby_games_kb(games, uid))

@router.message(F.text.func(lambda t: (t or '').strip().startswith("ساخت بازی روبی")))
async def create_ruby_command(message: Message):
    u = await get_user(message.from_user.id)
    if u["level"] < RUBY_CREATE_MIN_LEVEL:
        return await message.answer("🔒 ساخت بازی روبی از لول ۳ باز می‌شود.")
    parts = message.text.strip().split()
    if len(parts) < 4:
        return await message.answer("❌ نمونه صحیح:\n<code>ساخت بازی روبی 100</code>")
    try:
        amount = parse_number(parts[-1])
    except Exception:
        return await message.answer("❌ مبلغ بازی باید عدد باشد.")
    ok, reason, gid = await create_ruby_game(message.from_user.id, amount)
    if not ok:
        msgs = {"amount": f"❌ مبلغ باید بین ۱ تا {RUBY_MAX_STAKE:,} روب‌پوینت باشد.", "level": "🔒 ساخت بازی از لول ۳ باز می‌شود.", "points": "❌ روب‌پوینت کافی برای ساخت این بازی نداری.", "existing": "❌ یک بازی فعال از قبل داری."}
        return await message.answer(msgs.get(reason, "❌ ساخت بازی انجام نشد."))
    await message.answer(f"✅ بازی روبی #{gid} ساخته شد.\n🏅 مبلغ ورود: {amount:,} روب‌پوینت\n\nهر کاربر لول ۲ به بالا می‌تواند به آن بپیوندد.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 دیدن بازی‌های روبی", callback_data="ruby_games")]
    ]))

@router.message(F.text == "بازی های روبی")
@router.message(F.text == "بازی‌های روبی")
@router.message(F.text == "/ruby_games")
async def ruby_games_message(message: Message):
    await show_ruby_games(message, message.from_user.id)

@router.callback_query(F.data == "ruby_games")
async def ruby_games_button(call: CallbackQuery):
    await show_ruby_games(call.message, call.from_user.id)
    await call.answer()

@router.callback_query(F.data.startswith("ruby_join:"))
async def ruby_join(call: CallbackQuery):
    gid = int(call.data.split(":", 1)[1])
    ok, reason, data = await join_ruby_game(call.from_user.id, gid)
    if not ok:
        msgs = {"not_found":"❌ این بازی دیگر فعال نیست.","self":"❌ نمی‌توانی به بازی خودت بپیوندی.","level":"🔒 پیوستن به بازی از لول ۲ باز می‌شود.","points":"❌ روب‌پوینت کافی نداری."}
        await call.answer(msgs.get(reason, "❌ پیوستن انجام نشد."), show_alert=True)
        return
    winner, pot, creator, joiner = data
    result_for_caller = "🎉 تو برنده شدی و جایزه را گرفتی!" if winner == call.from_user.id else "😔 این بازی را باختی."
    await call.message.answer(
        f"🎮 بازی #{gid} تمام شد!\n\n"
        f"🏅 جایزه نهایی: {pot:,} روب‌پوینت\n"
        f"{result_for_caller}\n\n"
        "مبلغ برنده به‌صورت خودکار واریز شد."
    )
    other = creator if call.from_user.id == joiner else joiner
    try:
        other_result = "🎉 تو برنده شدی و جایزه را گرفتی!" if winner == other else "😔 این بازی را باختی."
        await call.bot.send_message(
            other,
            f"🎮 <b>نتیجه بازی روبی #{gid}</b>\n\n🏅 جایزه نهایی: {pot:,} روب‌پوینت\n{other_result}"
        )
    except Exception:
        pass
    await call.answer("بازی انجام شد")

@router.callback_query(F.data.startswith("ruby_cancel:"))
async def ruby_cancel(call: CallbackQuery):
    gid = int(call.data.split(":", 1)[1])
    if await cancel_ruby_game(call.from_user.id, gid):
        await call.message.answer("✅ بازی لغو شد و مبلغ ورود به موجودی سازنده برگشت.")
    else:
        await call.answer("❌ این بازی برای تو نیست یا قبلاً تمام شده.", show_alert=True)
        return
    await call.answer()
