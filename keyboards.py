
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import REQUIRED_CHANNEL_URL

def join_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 عضویت در کانال", url=REQUIRED_CHANNEL_URL)],
        [InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_join")]
    ])

def main_menu():
    items = [
        ("❓ شروع و دستورات","help"),("⭐ سطح کاربران","level"),
        ("🏆 رتبه‌بندی","ranking"),
        ("🦊 روبی و تولید","breeding"),("🪰 حشرات و یخچال","insects"),
        ("💳 بانک و انتقال","bank"),("👑 شهر روبی 🦊","city"),
        ("🦊 روباه","fox"),
        ("🎴 کازینو و بازی","games"),
        ("💎 بازی‌های روبی","ruby_games"),("🎲 شرط‌بندی فوتبال","football"),
        ("⚡ کارخانه","factory"),("⛓️ زندان و ضداسپم","jail"),
        ("🪙 نوشتن مبالغ","amounts"),("🛡️ تیم مدیریت","staff"),
        ("💳 وام بانکی","loan"),("🦊 قاچاق روبی","smuggle"),
        ("⌗ بازی دوز","tictactoe"),("🦊 مارکت روبی 🦊","market"),
        ("👑 رافل","raffle"),("🆚 جفت‌سازی و تولید","marriage"),
        ("🧸 خرید روبی پوینت","points"),("🔔 جایزه روزانه","daily"),
        ("🔄 چرخ شانس","wheel"),("🏅 ماموریت‌ها","missions"),
        ("🦊 هوهو (روب پوینت)","hoohoo"),("🏹 شکار","hunt"),
    ]
    rows = []
    for i in range(0, len(items), 2):
        row = [InlineKeyboardButton(text=items[i][0], callback_data=items[i][1])]
        if i + 1 < len(items):
            row.append(InlineKeyboardButton(text=items[i+1][0], callback_data=items[i+1][1]))
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

def back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu")]
    ])

def smuggle_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼 قابچی روبی", callback_data="market_frames")],
        [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu")]
    ])

def level_kb():
    return back_menu()

def daily_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 دریافت جایزه", callback_data="daily_claim")],
        [InlineKeyboardButton(text="🔙 منو", callback_data="menu")]
    ])

def missions_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 دریافت پاداش ماموریت", callback_data="mission_claim")],
        [InlineKeyboardButton(text="🔙 منو", callback_data="menu")]
    ])

def market_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪙 بسته کوچک", callback_data="buy_item:small"),
         InlineKeyboardButton(text="💎 بسته بزرگ", callback_data="buy_item:large")],
        [InlineKeyboardButton(text="🔙 منو", callback_data="menu")]
    ])

def frame_kb(frames):
    rows = []
    for f in frames:
        if f["owned"]:
            action = ("🟢 فعال" if f["owned_active"] else "⚪ فعال‌سازی",
                      f"frame_off:{f['id']}" if f["owned_active"] else f"frame_set:{f['id']}")
            rows.append([InlineKeyboardButton(text=f"🖼 {f['name']} — {action[0]}", callback_data=action[1])])
        else:
            rows.append([InlineKeyboardButton(text=f"🖼 {f['name']} • {f['price']} سکه", callback_data=f"frame_buy:{f['id']}")])
    rows.append([InlineKeyboardButton(text="🖼 قاب‌های من", callback_data="my_frames")])
    rows.append([InlineKeyboardButton(text="🔙 منو", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def frame_owned_kb(frames):
    rows=[]
    for f in frames:
        if f["owned"]:
            label = "🟢 فعال" if f["active"] else "⚪ فعال‌سازی"
            rows.append([InlineKeyboardButton(text=f"{f['name']} — {label}", callback_data=f"frame_set:{f['id']}" if not f["active"] else f"frame_off:{f['id']}")])
    rows.append([InlineKeyboardButton(text="🛒 فروشگاه قاب‌ها", callback_data="market_frames")])
    rows.append([InlineKeyboardButton(text="🔙 منو", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def loan_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 درخواست وام ۱۰۰۰", callback_data="loan_take")],
        [InlineKeyboardButton(text="💳 بازپرداخت وام", callback_data="loan_repay")],
        [InlineKeyboardButton(text="🔙 منو", callback_data="menu")]
    ])

def points_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧸 تبدیل ۱۰۰۰ سکه → ۱۰ پوینت", callback_data="points_buy")],
        [InlineKeyboardButton(text="🔙 منو", callback_data="menu")]
    ])

def factory_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ تولید", callback_data="factory_collect")],
        [InlineKeyboardButton(text="⬆️ ارتقای کارخانه", callback_data="factory_upgrade")],
        [InlineKeyboardButton(text="🔙 منو", callback_data="menu")]
    ])

def wheel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 چرخاندن", callback_data="wheel_spin")],
        [InlineKeyboardButton(text="🔙 منو", callback_data="menu")]
    ])

def catch_kb():
    # Hunting is intentionally isolated: no main-menu button while deciding.
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧊 گذاشتن در یخچال روبی", callback_data="catch:fridge")],
        [InlineKeyboardButton(text="🦊 دادن به روباه", callback_data="catch:fox")],
        [InlineKeyboardButton(text="💰 فروختن", callback_data="catch:sell")]
    ])

def ttt_kb(board):
    rows=[]
    for r in range(3):
        row=[]
        for c in range(3):
            v=board[r*3+c]
            row.append(InlineKeyboardButton(text=v or "·", callback_data=f"ttt:{r*3+c}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="🔙 منو", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
