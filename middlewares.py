import time
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from config import REQUIRED_CHANNEL
from keyboards import join_kb
from request_context import current_request, message_owners, INTERACTION_TTL
from db import ensure_user
from config import ADMIN_IDS

JOIN_TEXT = (
    "🔒 <b>عضویت اجباری</b>\n\n"
    "برای استفاده از ربات، ابتدا عضو کانال شو 🦊\n\n"
    f"📢 کانال: {REQUIRED_CHANNEL}\n\n"
    "بعد از عضویت، روی «✅ عضو شدم» بزن."
)

# فقط عضویت تأییدشده را کوتاه‌مدت کش می‌کنیم؛ نتیجه منفی کش نمی‌شود
# تا کاربر بلافاصله بعد از عضویت بتواند دوباره بررسی کند.
_positive_cache = {}
_CACHE_TTL = 20

async def is_member(bot, user_id: int):
    now = time.time()
    cached = _positive_cache.get(user_id)
    if cached and now - cached < _CACHE_TTL:
        return True
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        status = str(member.status).lower()
        ok = status in {"creator", "administrator", "member"}
        if status == "restricted" and getattr(member, "is_member", False):
            ok = True
        if ok:
            _positive_cache[user_id] = now
        return ok
    except (TelegramBadRequest, TelegramForbiddenError):
        return False
    except Exception:
        return False

def clear_membership_cache(user_id: int):
    _positive_cache.pop(user_id, None)

class UserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        # ثبت کاربر قبل از اجرای هر Handler؛ بدون این مرحله بسیاری از
        # قابلیت‌های اقتصادی چون get_user چیزی پیدا نمی‌کنند.
        await ensure_user(user)

        # هر دکمه فقط برای کاربری معتبر است که پیام ربات را گرفته است.
        if isinstance(event, CallbackQuery) and event.message and not (event.data or "").startswith(("ruby_join:", "ruby_games", "ruby_cancel:")):
            owner = message_owners.get(event.message.message_id)
            # اگر ربات ری‌استارت شده باشد، مالکیت را از reply_to_message خود پیام ربات هم می‌خوانیم.
            if owner is None and event.message.reply_to_message and event.message.reply_to_message.from_user:
                original = event.message.reply_to_message
                owner = (original.from_user.id, original.message_id, time.time())
            if owner and owner[0] != user.id:
                await event.answer("⛔ این گزینه برای کاربر دیگری است.", show_alert=True)
                return
            if owner and time.time() - owner[2] > INTERACTION_TTL:
                await event.answer("⌛ زمان این گزینه تمام شده است. دوباره دستور را بفرست.", show_alert=True)
                return

        token = None
        if isinstance(event, Message):
            token = current_request.set({
                "user_id": user.id,
                "message_id": event.message_id,
                "chat_id": event.chat.id,
            })
        elif isinstance(event, CallbackQuery):
            owner = None if (event.data or "").startswith(("ruby_join:", "ruby_games", "ruby_cancel:")) else (message_owners.get(event.message.message_id) if event.message else None)
            if owner is None and event.message and event.message.reply_to_message and event.message.reply_to_message.from_user:
                original = event.message.reply_to_message
                owner = (original.from_user.id, original.message_id, time.time())
            if owner:
                token = current_request.set({
                    "user_id": owner[0],
                    "message_id": owner[1],
                    "chat_id": event.message.chat.id if event.message else 0,
                })
            else:
                token = current_request.set({
                    "user_id": user.id,
                    "message_id": event.message.message_id if event.message else 0,
                    "chat_id": event.message.chat.id if event.message else 0,
                })
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

        # مدیر اصلی نباید به‌خاطر عضویت اجباری از پنل مدیریت بیرون انداخته شود.
        if user.id in ADMIN_IDS:
            return await handler(event, data)

        # دکمه «عضو شدم» باید همیشه به Handler برسد تا بررسی تازه انجام شود.
        if isinstance(event, CallbackQuery) and event.data == "check_join":
            return await handler(event, data)

        if await is_member(bot, user.id):
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            await event.answer("❌ هنوز عضویتت تأیید نشده. بعد از عضویت دوباره بزن.", show_alert=True)
            if event.message:
                try:
                    await event.message.answer(JOIN_TEXT, reply_markup=join_kb())
                except Exception:
                    pass
            return
        if isinstance(event, Message):
            await event.answer(JOIN_TEXT, reply_markup=join_kb())
            return
