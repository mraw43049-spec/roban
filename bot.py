
from aiogram import Bot
from aiogram.methods import SendMessage
from aiogram.types import ReplyParameters
from request_context import current_request, message_owners
import time

class ReplyingBot(Bot):
    async def __call__(self, method, request_timeout=None):
        req = current_request.get()
        if req and isinstance(method, SendMessage) and str(getattr(method, "chat_id", "")) == str(req.get("chat_id", "")):
            # Do not overwrite an explicit Telegram reply.
            if getattr(method, "reply_parameters", None) is None:
                method = method.model_copy(
                    update={"reply_parameters": ReplyParameters(message_id=req["message_id"])}
                )
        result = await super().__call__(method, request_timeout=request_timeout)

        # Remember who owns every outgoing bot message so its buttons cannot
        # be used by another user during this process lifetime.
        if req and isinstance(result, object) and hasattr(result, "message_id"):
            mid = getattr(result, "message_id", None)
            if mid:
                message_owners[mid] = (req["user_id"], req["message_id"], int(time.time()))
        return result
