from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    items = [
        ("❓ شروع و دستورات","help"),("⭐ سطح کاربران","level"),
        ("🦊 روبی و تولید","breeding"),("🪰 حشرات و یخچال","insects"),
        ("💳 بانک و انتقال","bank"),("👑 شهر روبی 🦊","city"),
        ("🎴 کازینو و بازی","games"),("🎲 شرط‌بندی فوتبال","football"),
        ("⚡ کارخانه","factory"),("⛓️ زندان و ضداسپم","jail"),
        ("🪙 نوشتن مبالغ","amounts"),("🛡️ تیم مدیریت","staff"),
        ("💳 وام بانکی","loan"),("🦊 قاچاق روبی","smuggle"),
        ("⌗ بازی دوز","tictactoe"),("🦊 مارکت روبی 🦊","market"),
        ("👑 رافل","raffle"),("🆚 جفت‌سازی و تولید","marriage"),
        ("🧸 خرید روبی پوینت","points"),("🔔 جایزه روزانه","daily"),
        ("🔄 چرخ شانس","wheel"),("🏅 ماموریت‌ها","missions"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=items[i][0],callback_data=items[i][1]),
         InlineKeyboardButton(text=items[i+1][0],callback_data=items[i+1][1])]
        for i in range(0,len(items),2)
    ])

def back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 بازگشت به منو",callback_data="menu")]
    ])
