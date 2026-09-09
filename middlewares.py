
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from config import REQUIRED_CHANNEL, REQUIRED_CHANNEL_URL
from keyboards import join_kb

JOIN_TEXT = (
    "🔒 <b>عضویت اجباری</b>\n\n"
    "برای استفاده از امکانات ربات، اول باید عضو کانال ما بشی 🦊\n\n"
    f"📢 کانال: {REQUIRED_CHANNEL}\n\n"
    "بعد از عضویت، روی دکمه «✅ عضو شدم» بزن."
)

# کش کوتاه‌مدت برای اینکه هر پیام یک درخواست جدید به تلگرام نزنیم
_cache = {}
_CACHE_TTL = 30


async def is_member(bot, user_id: int) -> bool:
    import time
    now = time.time()
    cached = _cache.get(user_id)
    if cached and now - cached[1] < _CACHE_TTL:
        return cached[0]
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        result = member.status in ("creator", "administrator", "member")
    except TelegramBadRequest:
        result = False
    except Exception:
        result = False
    _cache[user_id] = (result, now)
    return result


class ForceJoinMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        bot = data.get("bot")

        if not user or not bot:
            return await handler(event, data)

        if await is_member(bot, user.id):
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            await event.answer("❌ هنوز عضو کانال نشدی!", show_alert=True)
            try:
                await event.message.answer(JOIN_TEXT, reply_markup=join_kb())
            except Exception:
                pass
            return
        elif isinstance(event, Message):
            await event.answer(JOIN_TEXT, reply_markup=join_kb())
            return

        return
