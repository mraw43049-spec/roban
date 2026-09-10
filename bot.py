from aiogram import Bot
from aiogram.methods import SendMessage
from aiogram.types import ReplyParameters
from request_context import current_request, message_owners
import time

class ReplyingBot(Bot):
    async def __call__(self, method, request_timeout=None):
        req = current_request.get()
        if req and isinstance(method, SendMessage) and str(getattr(method, "chat_id", "")) == str(req.get("chat_id", "")):
            if getattr(method, "reply_parameters", None) is None:
                method = method.model_copy(update={"reply_parameters": ReplyParameters(message_id=req["message_id"])})
        result = await super().__call__(method, request_timeout=request_timeout)
        if req and hasattr(result, "message_id"):
            mid = getattr(result, "message_id", None)
            if mid:
                message_owners[mid] = (req["user_id"], req["message_id"], time.time())
        return result
