
import time
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from config import REQUIRED_CHANNEL
from keyboards import join_kb
from request_context import current_request, message_owners, INTERACTION_TTL

JOIN_TEXT = (
    "🔒 <b>عضویت اجباری</b>\n\n"
    "برای استفاده از امکانات ربات، اول باید عضو کانال ما بشی 🦊\n\n"
    f"📢 کانال: {REQUIRED_CHANNEL}\n\n"
    "بعد از عضویت، روی دکمه «✅ عضو شدم» بزن."
)
_cache = {}
_CACHE_TTL = 30

async def is_member(bot, user_id: int) -> bool:
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

class UserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        bot = data.get("bot")
        if not user:
            return await handler(event, data)

        # Every callback belongs only to the user whose command/message
        # originally created the bot message.
        if isinstance(event, CallbackQuery) and event.message:
            owner = message_owners.get(event.message.message_id)
            if owner and (owner[0] != user.id or time.time() - owner[2] > INTERACTION_TTL):
                await event.answer("⛔ این گزینه برای کاربر دیگری است یا مهلتش تمام شده.", show_alert=True)
                return

        token = None
        if isinstance(event, Message):
            token = current_request.set({"user_id": user.id, "message_id": event.message_id, "chat_id": event.chat.id})
        elif isinstance(event, CallbackQuery):
            owner = message_owners.get(event.message.message_id)
            if owner:
                token = current_request.set({"user_id": owner[0], "message_id": owner[1], "chat_id": event.message.chat.id if event.message else 0})
            else:
                token = current_request.set({"user_id": user.id, "message_id": event.message.message_id if event.message else 0})

        try:
            return await handler(event, data)
        finally:
            if token:
                current_request.reset(token)

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
        if isinstance(event, Message):
            await event.answer(JOIN_TEXT, reply_markup=join_kb())
            return
