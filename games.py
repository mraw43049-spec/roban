from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
try:
    from app.db import update_xp
except ModuleNotFoundError:
    from db import update_xp
try:
    from app.keyboards import back_menu
except ModuleNotFoundError:
    from keyboards import back_menu

router=Router()

@router.callback_query(F.data=="tictactoe")
async def ttt_button(call: CallbackQuery):
    await call.message.answer("⌗ بازی دوز\n\nبرای شروع /tictactoe را بزن.", reply_markup=back_menu())
    await call.answer()

@router.message(F.text=="/tictactoe")
async def ttt(message: Message):
    await update_xp(message.from_user.id,10)
    await message.answer("⌗ <b>بازی دوز</b>\n\nنسخه پایه آماده است و می‌توان موتور چندنفره را روی همین ساختار اضافه کرد.\n✨ +10 XP", reply_markup=back_menu())
