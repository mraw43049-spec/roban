from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.keyboards import main_menu, back_menu
from app.texts import MENU_TEXT, SECTIONS, profile_text
from app.db import get_user

router = Router()

@router.message(F.text.in_({"/start","/menu"}))
async def start(message: Message):
    await message.answer(MENU_TEXT, reply_markup=main_menu())

@router.message(F.text == "/help")
async def help_cmd(message: Message):
    await message.answer(SECTIONS["help"], reply_markup=back_menu())

@router.message(F.text == "/profile")
async def profile(message: Message):
    await message.answer(profile_text(await get_user(message.from_user.id)), reply_markup=back_menu())

@router.callback_query(F.data == "menu")
async def menu_callback(call: CallbackQuery):
    await call.message.edit_text(MENU_TEXT, reply_markup=main_menu())
    await call.answer()

@router.callback_query(F.data.in_(SECTIONS.keys()))
async def section_callback(call: CallbackQuery):
    await call.message.edit_text(SECTIONS[call.data], reply_markup=back_menu())
    await call.answer()
