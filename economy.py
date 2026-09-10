
import time
import random
import uuid
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import (
    get_user, set_daily, change_coins, spend_coins, update_xp, transfer_points,
    list_frames, buy_frame, set_active_frame, disable_frame, get_active_frame,
    mission_progress, get_missions, claim_mission, change_points
)
from keyboards import (
    back_menu, daily_kb, missions_kb, market_kb, frame_kb, frame_owned_kb,
    loan_kb, points_kb, factory_kb, wheel_kb, smuggle_kb
)

router = Router()

async def show_level(target, uid):
    u = await get_user(uid)
    await target.answer(
        """╭──「 📚 سطح کاربران 」
└─ بخش 1 از 10

🏫 آکادمی روباهیو 🦊
┘─ 🐾 بخش: سیستم روباهیو ⚙️
┘─ 📚 مطلب: سطح کاربران 🐾

✨ روبی‌های مورد نیاز، تعداد تجمعی روبی برای رسیدن به سطح است.
✨ پوینت دریافتی، بازه جایزه هر روبی است.
✨ زمان استراحت با باف شهر می‌تواند کمتر شود.
✨ جایزه ارتقا هنگام رسیدن به سطح خودکار واریز می‌شود.

〰️〰️〰️〰️〰️〰️〰️

⭐️ سطح 1
┘─ 💤 روبی‌های مورد نیاز: 0
┘─ 💰 پوینت دریافتی: 5 تا 15 🪙
┘─ ⏳ زمان استراحت: 5:00
┘─ 💝 جایزه ارتقا: 0 🪙

〰️〰️〰️〰️〰️〰️〰️

⭐️ سطح 2
┘─ 💤 روبی‌های مورد نیاز: 5
┘─ 💰 پوینت دریافتی: 10 تا 20 🪙
┘─ ⏳ زمان استراحت: 5:00
┘─ 💝 جایزه ارتقا: 50 🪙
🔓 قابلیت‌های جدید
┘─ شکار حشرات
┘─ پیوستن به بازی
┘─ دریافت انتقال

〰️〰️〰️〰️〰️〰️〰️

⭐️ سطح 3
┘─ 💤 روبی‌های مورد نیاز: 15
┘─ 💰 پوینت دریافتی: 15 تا 25 🪙
┘─ ⏳ زمان استراحت: 5:00
┘─ 💝 جایزه ارتقا: 225 🪙
🔓 قابلیت‌های جدید
┘─ روباه
┘─ ساخت بازی
┘─ انتقال روب پوینت

〰️〰️〰️〰️〰️〰️〰️

⭐️ سطح 4
┘─ 💤 روبی‌های مورد نیاز: 40
┘─ 💰 پوینت دریافتی: 20 تا 35 🪙
┘─ ⏳ زمان استراحت: 5:00
┘─ 💝 جایزه ارتقا: 500 🪙
🔓 قابلیت‌های جدید
┘─ بانک
┘─ پیوستن به کازینو

〰️〰️〰️〰️〰️〰️〰️

⭐️ سطح 5
┘─ 💤 روبی‌های مورد نیاز: 75
┘─ 💰 پوینت دریافتی: 25 تا 40 🪙
┘─ ⏳ زمان استراحت: 4:55
┘─ 💝 جایزه ارتقا: 1,000 🪙
🔓 قابلیت‌های جدید
┘─ ساخت کازینو


╰─ 📄 صفحه 1 از 10""",
        reply_markup=back_menu()
    )

@router.callback_query(F.data == "level")
async def level_button(call: CallbackQuery):
    await show_level(call.message, call.from_user.id)
    await call.answer()

@router.message(F.text == "/level")
async def level_cmd(message: Message):
    await show_level(message, message.from_user.id)

async def daily_action(target, uid):
    u = await get_user(uid)
    now = int(time.time())
    remain = 86400 - (now - u["last_daily"])
    if remain > 0:
        await target.answer(
            f"🔔 جایزه امروز قبلاً گرفته شده.\n"
            f"⏳ {remain//3600} ساعت و {(remain%3600)//60} دقیقه باقی مانده.",
            reply_markup=daily_kb()
        )
        return
    await set_daily(uid, now, 100)
    await update_xp(uid, 20)
    await mission_progress(uid, "daily", 1, 1)
    await target.answer("🎁 +100 سکه\n✨ +20 XP\n\nماموریت ورود روزانه کامل شد.", reply_markup=daily_kb())

@router.callback_query(F.data == "daily")
async def daily_button(call: CallbackQuery):
    await daily_action(call.message, call.from_user.id)
    await call.answer()

@router.callback_query(F.data == "daily_claim")
async def daily_claim(call: CallbackQuery):
    await daily_action(call.message, call.from_user.id)
    await call.answer()

@router.message(F.text == "/daily")
async def daily_cmd(message: Message):
    await daily_action(message, message.from_user.id)

async def missions_text(uid):
    rows = await get_missions(uid)
    names = {"daily":"ورود روزانه", "game":"انجام یک بازی", "market":"باز کردن مارکت"}
    if not rows:
        return "🏅 <b>ماموریت‌ها</b>\n\nهنوز ماموریتی ثبت نشده. یک بازی یا مارکت را باز کن."
    out = ["🏅 <b>ماموریت‌ها</b>", ""]
    for r in rows:
        status = "✅ دریافت شده" if r["claimed"] else ("🎁 آماده دریافت" if r["progress"] >= r["target"] else f"⏳ {r['progress']}/{r['target']}")
        out.append(f"• {names.get(r['mission'],r['mission'])}: {status}")
    out.append("\n🎁 هر ماموریت کامل = 150 سکه")
    return "\n".join(out)

@router.callback_query(F.data == "missions")
async def missions_button(call: CallbackQuery):
    await call.message.answer(await missions_text(call.from_user.id), reply_markup=missions_kb())
    await call.answer()

@router.message(F.text == "/missions")
async def missions_cmd(message: Message):
    await message.answer(await missions_text(message.from_user.id), reply_markup=missions_kb())

@router.callback_query(F.data == "mission_claim")
async def mission_claim_button(call: CallbackQuery):
    total = 0
    for name in ("daily", "game", "market"):
        if await claim_mission(call.from_user.id, name, 150):
            total += 150
    await call.message.answer(f"🎁 {total} سکه به‌عنوان پاداش ماموریت دریافت شد." if total else "❌ ماموریت آماده‌ای برای دریافت نداری.", reply_markup=missions_kb())
    await call.answer()

pending_transfers = {}
TRANSFER_MAX = 500_000
TRANSFER_MIN_LEVEL = 2
TRANSFER_EXPIRE = 60

def transfer_kb(token):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ تایید", callback_data=f"tr_ok:{token}"),
         InlineKeyboardButton(text="❌ لغو", callback_data=f"tr_cancel:{token}")]
    ])

async def bank_text(uid):
    u = await get_user(uid)
    return (
        f"💳 <b>بانک و انتقال روب پوینت</b>\n\n"
        f"🏅 روب پوینت: {u['points']:,}\n⭐ لول: {u['level']}\n\n"
        "برای انتقال، روی پیام کاربر مقصد ریپلای کن و بنویس:\n"
        "<code>انتقال 50 روب پوینت</code>\n\n"
        "🔒 انتقال از لول ۲ باز است.\n"
        f"📌 سقف هر انتقال: {TRANSFER_MAX:,} روب پوینت\n"
        "⏱️ تایید انتقال فقط ۶۰ ثانیه معتبر است."
    )

@router.callback_query(F.data == "bank")
async def bank_button(call: CallbackQuery):
    await call.message.answer(await bank_text(call.from_user.id), reply_markup=back_menu())
    await call.answer()

@router.message(F.text == "/bank")
async def bank_cmd(message: Message):
    await message.answer(await bank_text(message.from_user.id), reply_markup=back_menu())

def _transfer_amount(text):
    parts = (text or "").strip().split()
    if len(parts) >= 2 and parts[0] == "انتقال":
        try:
            return int(parts[1])
        except ValueError:
            return None
    if len(parts) == 3 and parts[0] == "/pay":
        try:
            return int(parts[2])
        except ValueError:
            return None
    return None

@router.message(F.text.func(lambda t: (t or "").strip().startswith("انتقال ")))
async def transfer_command(message: Message):
    uid = message.from_user.id
    u = await get_user(uid)
    if u["level"] < TRANSFER_MIN_LEVEL:
        return await message.answer("🔒 انتقال روب پوینت از لول ۲ باز می‌شود.", reply_markup=back_menu())

    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.answer(
            "❌ برای انتقال باید روی پیام خودِ کاربر مقصد ریپلای کنی.\n"
            "مثال: روی پیامش ریپلای کن و بنویس «انتقال 50 روب پوینت».",
            reply_markup=back_menu()
        )

    target = message.reply_to_message.from_user
    target_id = target.id
    if target_id == uid:
        return await message.answer("❌ نمی‌توانی به خودت انتقال بدهی.", reply_markup=back_menu())

    amount = _transfer_amount(message.text)
    if amount is None or amount <= 0:
        return await message.answer("❌ مبلغ نامعتبر است.", reply_markup=back_menu())
    if amount > TRANSFER_MAX:
        return await message.answer(f"❌ سقف هر انتقال {TRANSFER_MAX:,} روب پوینت است.", reply_markup=back_menu())

    recipient = await get_user(target_id)
    if not recipient:
        return await message.answer("❌ کاربر مقصد هنوز ربات را فعال نکرده است.", reply_markup=back_menu())
    if u["points"] < amount:
        return await message.answer(f"❌ موجودی کافی نیست.\n🏅 موجودی: {u['points']:,}", reply_markup=back_menu())

    token = uuid.uuid4().hex[:12]
    pending_transfers[token] = {
        "sender": uid, "receiver": target_id, "amount": amount,
        "created": int(time.time()), "message_id": message.message_id
    }
    await message.answer(
        f"💸 <b>تأیید انتقال</b>\n\n"
        f"👤 مقصد: {target.first_name or 'کاربر'}\n"
        f"🏅 مبلغ: {amount:,} روب پوینت\n\n"
        "این انتقال تا ۶۰ ثانیه معتبر است.",
        reply_markup=transfer_kb(token)
    )

@router.callback_query(F.data.startswith("tr_"))
async def transfer_decision(call: CallbackQuery):
    _, action, token = call.data.split(":", 2)
    item = pending_transfers.get(token)
    if not item:
        await call.answer("⌛ زمان این انتقال تمام شده.", show_alert=True)
        return
    if int(time.time()) - item["created"] > TRANSFER_EXPIRE:
        pending_transfers.pop(token, None)
        await call.message.edit_text("⌛ زمان تأیید انتقال تمام شد.")
        await call.answer()
        return
    if call.from_user.id != item["sender"]:
        await call.answer("⛔ این انتقال برای کاربر دیگری است.", show_alert=True)
        return

    pending_transfers.pop(token, None)
    if action == "cancel":
        await call.message.edit_text("❌ انتقال لغو شد.")
        await call.answer("لغو شد")
        return

    ok, _ = await transfer_points(item["sender"], item["receiver"], item["amount"])
    if not ok:
        await call.message.edit_text("❌ انتقال انجام نشد؛ موجودی یا شرایط انتقال تغییر کرده است.")
        await call.answer()
        return
    await call.message.edit_text(
        f"✅ انتقال انجام شد.\n🏅 {item['amount']:,} روب پوینت به کاربر مقصد منتقل شد."
    )
    await call.answer("انتقال انجام شد")

async def market_action(target, uid):
    await mission_progress(uid, "market", 1, 1)
    u = await get_user(uid)
    await target.answer(
        f"🦊 <b>مارکت روبی</b>\n\n🪙 موجودی: {u['coins']} سکه\n\n"
        "📦 بسته کوچک — 250 سکه → 5 روبی\n"
        "💎 بسته بزرگ — 1000 سکه → 25 روبی\n\n"
        "خریدها داخل موجودی مجازی ربات ثبت می‌شوند.",
        reply_markup=market_kb()
    )

@router.callback_query(F.data == "market")
async def market_button(call: CallbackQuery):
    await market_action(call.message, call.from_user.id)
    await call.answer()

@router.message(F.text == "/market")
async def market_cmd(message: Message):
    await market_action(message, message.from_user.id)

@router.callback_query(F.data.startswith("buy_item:"))
async def buy_item(call: CallbackQuery):
    kind = call.data.split(":")[1]
    if kind == "small":
        cost, qty = 250, 5
    else:
        cost, qty = 1000, 25
    if not await spend_coins(call.from_user.id, cost):
        await call.message.answer("❌ سکه کافی نیست.", reply_markup=market_kb())
    else:
        await change_points(call.from_user.id, qty)
        await update_xp(call.from_user.id, 5)
        await call.message.answer(f"✅ خرید انجام شد.\n💎 +{qty} روبی پوینت\n🪙 -{cost} سکه", reply_markup=market_kb())
    await call.answer()

@router.callback_query(F.data == "factory")
async def factory_button(call: CallbackQuery):
    u = await get_user(call.from_user.id)
    level = u["factory_level"]
    cost = level * 1000
    await call.message.answer(
        f"⚡ <b>کارخانه</b>\n\nسطح: {level}\n"
        f"تولید ساعتی: {level*100} سکه\n"
        f"ارتقای بعدی: {cost} سکه",
        reply_markup=factory_kb()
    )
    await call.answer()

@router.message(F.text == "/factory")
async def factory_cmd(message: Message):
    await factory_button(await _fake_callback(message))  # unreachable helper below


async def factory_action(target, uid):
    u = await get_user(uid)
    level = u["factory_level"]
    cost = level * 1000
    await target.answer(
        f"⚡ <b>کارخانه</b>\n\n🏭 سطح: {level}\n"
        f"📦 تولید: {level*100} سکه در هر ساعت\n"
        f"⬆️ هزینه ارتقا: {cost} سکه",
        reply_markup=factory_kb()
    )

@router.message(F.text == "/factory")
async def factory_cmd(message: Message):
    await factory_action(message, message.from_user.id)

@router.callback_query(F.data == "factory_collect")
async def factory_collect(call: CallbackQuery):
    u = await get_user(call.from_user.id)
    now = int(time.time())
    elapsed = max(0, now-u["factory_last"])
    hours = elapsed // 3600
    if hours < 1:
        await call.message.answer("⏳ هنوز یک ساعت کامل نشده.", reply_markup=factory_kb())
    else:
        hours = min(hours, 24)
        reward = hours * u["factory_level"] * 100
        await change_coins(call.from_user.id, reward)
        await update_xp(call.from_user.id, 5)
        import aiosqlite
        from config import DB_PATH
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET factory_last=? WHERE user_id=?", (now,call.from_user.id))
            await db.commit()
        await call.message.answer(f"⚡ تولید جمع‌آوری شد: +{reward} سکه\n✨ +5 XP", reply_markup=factory_kb())
    await call.answer()

@router.callback_query(F.data == "factory_upgrade")
async def factory_upgrade(call: CallbackQuery):
    u = await get_user(call.from_user.id)
    cost = u["factory_level"] * 1000
    if not await spend_coins(call.from_user.id, cost):
        await call.message.answer(f"❌ سکه کافی نیست. نیاز: {cost}", reply_markup=factory_kb())
    else:
        import aiosqlite
        from config import DB_PATH
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET factory_level=factory_level+1 WHERE user_id=?", (call.from_user.id,))
            await db.commit()
        await update_xp(call.from_user.id, 20)
        await call.message.answer("✅ کارخانه یک سطح ارتقا پیدا کرد.\n✨ +20 XP", reply_markup=factory_kb())
    await call.answer()

@router.callback_query(F.data == "wheel")
async def wheel_button(call: CallbackQuery):
    await call.message.answer("🔄 <b>چرخ شانس</b>\n\nبا چرخاندن، یک جایزه مجازی می‌گیری.", reply_markup=wheel_kb())
    await call.answer()

@router.message(F.text == "/wheel")
async def wheel_cmd(message: Message):
    await message.answer("🔄 <b>چرخ شانس</b>\n\nیک جایزه مجازی تصادفی بگیر.", reply_markup=wheel_kb())

@router.callback_query(F.data == "wheel_spin")
async def wheel_spin(call: CallbackQuery):
    cost = 50
    if not await spend_coins(call.from_user.id, cost):
        await call.message.answer("❌ برای چرخاندن ۵۰ سکه لازم داری.", reply_markup=wheel_kb())
    else:
        prize = random.choice([0, 25, 50, 75, 100, 150, 250])
        await change_coins(call.from_user.id, prize)
        await update_xp(call.from_user.id, 10)
        await mission_progress(call.from_user.id, "game", 1, 1)
        await call.message.answer(f"🎡 نتیجه: +{prize} سکه\n🪙 هزینه: {cost} سکه\n✨ +10 XP", reply_markup=wheel_kb())
    await call.answer()

@router.callback_query(F.data == "loan")
async def loan_button(call: CallbackQuery):
    u = await get_user(call.from_user.id)
    status = f"وام فعلی: {u['loan']} سکه" if u["loan"] else "وام فعالی نداری."
    await call.message.answer(f"💳 <b>وام بانکی</b>\n\n{status}\n\nسقف وام: ۱۰۰۰ سکه", reply_markup=loan_kb())
    await call.answer()

@router.callback_query(F.data == "loan_take")
async def loan_take(call: CallbackQuery):
    u = await get_user(call.from_user.id)
    if u["loan"] > 0:
        msg = "❌ هنوز وام قبلی تسویه نشده."
    else:
        import aiosqlite
        from config import DB_PATH
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET loan=1000,loan_due=? WHERE user_id=?", (int(time.time())+7*86400,call.from_user.id))
            await db.execute("UPDATE users SET coins=coins+1000 WHERE user_id=?", (call.from_user.id,))
            await db.commit()
        msg = "✅ ۱۰۰۰ سکه وام گرفتی. مهلت بازپرداخت: ۷ روز."
    await call.message.answer(msg, reply_markup=loan_kb())
    await call.answer()

@router.callback_query(F.data == "loan_repay")
async def loan_repay(call: CallbackQuery):
    u = await get_user(call.from_user.id)
    if u["loan"] <= 0:
        msg = "ℹ️ وام فعالی نداری."
    elif await spend_coins(call.from_user.id, u["loan"]):
        import aiosqlite
        from config import DB_PATH
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET loan=0,loan_due=0 WHERE user_id=?", (call.from_user.id,))
            await db.commit()
        msg = "✅ وام کامل تسویه شد."
    else:
        msg = f"❌ برای تسویه {u['loan']} سکه لازم داری."
    await call.message.answer(msg, reply_markup=loan_kb())
    await call.answer()

@router.callback_query(F.data == "points")
async def points_button(call: CallbackQuery):
    u = await get_user(call.from_user.id)
    await call.message.answer(f"🧸 <b>روبی پوینت</b>\n\n🪙 سکه: {u['coins']}\n🏅 پوینت: {u['points']}", reply_markup=points_kb())
    await call.answer()

@router.callback_query(F.data == "points_buy")
async def points_buy(call: CallbackQuery):
    if await spend_coins(call.from_user.id, 1000):
        await change_points(call.from_user.id, 10)
        await call.message.answer("✅ ۱۰ روبی پوینت خریدی و ۱۰۰۰ سکه پرداخت شد.", reply_markup=points_kb())
    else:
        await call.message.answer("❌ سکه کافی نیست.", reply_markup=points_kb())
    await call.answer()

@router.callback_query(F.data == "market_frames")
async def frame_market(call: CallbackQuery):
    frames = await list_frames(call.from_user.id)
    await call.message.answer("🦊 <b>قابچی روبی</b>\n\nقاب موردنظر را بخر یا فعال کن:", reply_markup=frame_kb(frames))
    await call.answer()

@router.callback_query(F.data == "smuggle")
async def smuggle(call: CallbackQuery):
    await call.message.answer("🦊 <b>قاچاق روبی</b>\n\nبرای تبادل مجازی آیتم‌ها آماده است.\nقاب‌های پروفایل را هم از همین‌جا مدیریت کن.", reply_markup=smuggle_kb())
    await call.answer()

@router.callback_query(F.data == "breeding")
async def breeding(call: CallbackQuery):
    await call.message.answer("🦊 <b>روبی و تولید</b>\n\nبا هر تولید ۱۰ روبی پوینت می‌گیری.\n\n/produce", reply_markup=back_menu())
    await call.answer()

@router.message(F.text == "/produce")
async def produce(message: Message):
    if await spend_coins(message.from_user.id, 100):
        await change_points(message.from_user.id, 10)
        await update_xp(message.from_user.id, 10)
        await message.answer("🦊 تولید انجام شد.\n💎 +10 پوینت\n🪙 -100 سکه", reply_markup=back_menu())
    else:
        await message.answer("❌ برای تولید ۱۰۰ سکه لازم داری.", reply_markup=back_menu())

@router.callback_query(F.data == "insects")
async def insects(call: CallbackQuery):
    await call.message.answer("🪰 <b>حشرات و یخچال</b>\n\nبرای دریافت آیتم مجازی:\n<code>/collect_insect</code>", reply_markup=back_menu())
    await call.answer()

@router.message(F.text == "/collect_insect")
async def collect_insect(message: Message):
    item = random.choice(["🪰 مگس","🦋 پروانه","🐞 کفشدوزک","🪲 سوسک"])
    import aiosqlite
    from config import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""INSERT INTO inventory(user_id,item,quantity) VALUES(?,?,1)
            ON CONFLICT(user_id,item) DO UPDATE SET quantity=quantity+1""",(message.from_user.id,item))
        await db.commit()
    await message.answer(f"🧊 آیتم جدید: {item}", reply_markup=back_menu())

@router.callback_query(F.data == "city")
async def city(call: CallbackQuery):
    u = await get_user(call.from_user.id)
    await call.message.answer(f"👑 <b>شهر روبی</b>\n\n🏠 شهر تو فعال است.\n🪙 سرمایه: {u['coins']}\n🏭 کارخانه: سطح {u['factory_level']}", reply_markup=back_menu())
    await call.answer()

@router.callback_query(F.data == "football")
async def football(call: CallbackQuery):
    await call.message.answer("🎲 <b>پیش‌بینی فوتبال</b>\n\nاین نسخه شبیه‌سازی تفریحی است و اطلاعات زنده مسابقات ندارد.\n\n/football home\n/football draw\n/football away", reply_markup=back_menu())
    await call.answer()

@router.message(F.text.startswith("/football"))
async def football_cmd(message: Message):
    parts = message.text.split()
    if len(parts) != 2 or parts[1] not in {"home","draw","away"}:
        return await message.answer("قالب: /football home | draw | away", reply_markup=back_menu())
    result = random.choice(["home","draw","away"])
    text = {"home":"برد میزبان","draw":"مساوی","away":"برد مهمان"}[result]
    pick = {"home":"برد میزبان","draw":"مساوی","away":"برد مهمان"}[parts[1]]
    await update_xp(message.from_user.id, 5)
    await mission_progress(message.from_user.id, "game", 1, 1)
    await message.answer(f"🎲 نتیجه شبیه‌سازی: {text}\nانتخاب تو: {pick}\n✨ +5 XP", reply_markup=back_menu())

@router.callback_query(F.data == "jail")
async def jail(call: CallbackQuery):
    await call.message.answer("⛓️ <b>زندان و ضداسپم</b>\n\nمدیریت پایه فعال است. تنظیمات پیشرفته ضداسپم را می‌توان از پنل مدیریت اضافه کرد.", reply_markup=back_menu())
    await call.answer()

@router.callback_query(F.data == "amounts")
async def amounts(call: CallbackQuery):
    await call.message.answer("🪙 <b>نوشتن مبالغ</b>\n\nبرای نمایش خوانای مبلغ:\n<code>/amount 125000</code>", reply_markup=back_menu())
    await call.answer()

@router.message(F.text.startswith("/amount "))
async def amount(message: Message):
    try:
        n=int(message.text.split()[1])
        if n<0: raise ValueError
        await message.answer(f"🪙 مبلغ: {n:,} سکه", reply_markup=back_menu())
    except Exception:
        await message.answer("قالب درست: /amount 125000", reply_markup=back_menu())

@router.callback_query(F.data == "raffle")
async def raffle_button(call: CallbackQuery):
    await call.message.answer("👑 <b>رافل تفریحی</b>\n\nورود رایگان است و فقط جایزه مجازی دارد.\n<code>/raffle_join</code>", reply_markup=back_menu())
    await call.answer()

@router.message(F.text == "/raffle")
async def raffle_cmd(message: Message):
    await message.answer("👑 رافل تفریحی فعال است.\nبرای ورود: /raffle_join", reply_markup=back_menu())

@router.message(F.text == "/raffle_join")
async def raffle_join(message: Message):
    await update_xp(message.from_user.id, 5)
    await message.answer("✅ وارد رافل تفریحی شدی.\n✨ +5 XP", reply_markup=back_menu())

@router.callback_query(F.data == "marriage")
async def marriage(call: CallbackQuery):
    await call.message.answer("🆚 <b>جفت‌سازی و تولید</b>\n\n<code>/pair USER_ID</code>\nهزینه: ۲۰۰ سکه؛ پاداش: ۲۵ پوینت.", reply_markup=back_menu())
    await call.answer()

@router.message(F.text.startswith("/pair "))
async def pair(message: Message):
    try:
        target=int(message.text.split()[1])
    except Exception:
        return await message.answer("قالب: /pair USER_ID", reply_markup=back_menu())
    if target == message.from_user.id:
        return await message.answer("❌ نمی‌توانی با خودت جفت‌سازی کنی.", reply_markup=back_menu())
    if not await get_user(target):
        return await message.answer("❌ کاربر پیدا نشد.", reply_markup=back_menu())
    if not await spend_coins(message.from_user.id, 200):
        return await message.answer("❌ ۲۰۰ سکه لازم داری.", reply_markup=back_menu())
    await change_points(message.from_user.id, 25)
    await update_xp(message.from_user.id, 15)
    await message.answer("🆚 جفت‌سازی انجام شد.\n💎 +25 پوینت\n✨ +15 XP", reply_markup=back_menu())

@router.callback_query(F.data == "staff")
async def staff(call: CallbackQuery):
    await call.message.answer("🛡️ <b>تیم مدیریت</b>\n\nمدیر می‌تواند:\n/admin\n/admin_add USER_ID AMOUNT", reply_markup=back_menu())
    await call.answer()

@router.callback_query(F.data == "games")
async def games(call: CallbackQuery):
    await call.message.answer("🎴 <b>کازینو و بازی</b>\n\nبازی‌های این نسخه با سکه مجازی هستند:\n🎲 /dice\n🔄 /wheel\n⌗ /tictactoe", reply_markup=back_menu())
    await call.answer()

@router.callback_query(F.data.startswith("frame_buy:"))
async def frame_buy(call: CallbackQuery):
    fid = int(call.data.split(":")[1])
    ok, reason = await buy_frame(call.from_user.id, fid)
    if ok:
        await update_xp(call.from_user.id, 10)
        await call.message.answer("✅ قاب خریداری شد.\nمالکیت قاب دائمی است و برای فعال‌کردن دوباره نیاز به خرید مجدد نداری.", reply_markup=back_menu())
    elif reason == "not_allowed":
        await call.message.answer("❌ قاب پیدا نشد، قبلاً خریداری شده یا سکه کافی نیست.", reply_markup=back_menu())
    await call.answer()

@router.callback_query(F.data.startswith("frame_set:"))
async def frame_set(call: CallbackQuery):
    fid=int(call.data.split(":")[1])
    if await set_active_frame(call.from_user.id,fid):
        f=await get_active_frame(call.from_user.id)
        await call.message.answer(f"🟢 قاب «{f['name']}» فعال شد.\nاین قاب در پروفایل، رتبه‌بندی، چت‌روم و بازی قابل استفاده است.", reply_markup=back_menu())
    else:
        await call.message.answer("❌ این قاب را هنوز نخریده‌ای.", reply_markup=back_menu())
    await call.answer()

@router.callback_query(F.data.startswith("frame_off:"))
async def frame_off(call: CallbackQuery):
    await disable_frame(call.from_user.id)
    await call.message.answer("⚪ قاب غیرفعال شد.\nمالکیت قاب حفظ شد و هر زمان بخواهی می‌توانی دوباره فعالش کنی.", reply_markup=back_menu())
    await call.answer()

@router.callback_query(F.data == "my_frames")
async def my_frames(call: CallbackQuery):
    frames = await list_frames(call.from_user.id)
    await call.message.answer("🖼 <b>قاب‌های من</b>\n\nقاب خریداری‌شده را فعال یا غیرفعال کن.", reply_markup=frame_owned_kb(frames))
    await call.answer()
