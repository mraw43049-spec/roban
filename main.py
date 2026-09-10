
import asyncio
from aiogram import Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from db import init_db, ensure_user
from handlers.menu import router as menu_router
from handlers.economy import router as economy_router
from handlers.games import router as games_router
from handlers.admin import router as admin_router
from handlers.hunting import router as hunting_router
from handlers.fox_ruby import router as fox_ruby_router
from middlewares import ForceJoinMiddleware, UserMiddleware
from bot import ReplyingBot

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set.")
    await init_db()
    bot = ReplyingBot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    dp.message.middleware(ForceJoinMiddleware())
    dp.callback_query.middleware(ForceJoinMiddleware())
    dp.include_router(menu_router)
    dp.include_router(economy_router)
    dp.include_router(games_router)
    dp.include_router(hunting_router)
    # مدیریت باید قبل از fox_ruby ثبت شود؛ fox_ruby یک handler عمومی F.text دارد.
    dp.include_router(admin_router)
    dp.include_router(fox_ruby_router)
    await bot.delete_webhook(drop_pending_updates=True)
    print("Gorbaw bot is running", flush=True)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
