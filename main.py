import asyncio
import os
from aiogram import Bot, Dispatcher, BaseMiddleware
from config import BOT_TOKEN
from db import init_db, ensure_user
from handlers.menu import router as menu_router
from handlers.economy import router as economy_router
from handlers.games import router as games_router
from handlers.admin import router as admin_router

class UserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user:
            await ensure_user(user)
        return await handler(event, data)

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set.")
    await init_db()
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    dp.include_router(menu_router)
    dp.include_router(economy_router)
    dp.include_router(games_router)
    dp.include_router(admin_router)
    await bot.delete_webhook(drop_pending_updates=True)
    print("Gorbaw bot is running", flush=True)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
