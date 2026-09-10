
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards import main_menu, back_menu
from texts import MENU_TEXT, SECTIONS, profile_text
from db import get_user, get_active_frame
import aiosqlite
from config import DB_PATH
from middlewares import is_member, clear_membership_cache

router = Router()
STATIC_KEYS = {"help"}

@router.message(F.text.in_({"/start","/menu"}))
async def start(message: Message):
    await message.answer(MENU_TEXT, reply_markup=main_menu())

@router.message(F.text == "/help")
async def help_cmd(message: Message):
    await message.answer(SECTIONS["help"], reply_markup=back_menu())

@router.message(F.text == "/profile")
async def profile(message: Message):
    u = await get_user(message.from_user.id)
    frame = await get_active_frame(message.from_user.id)
    await message.answer(profile_text(u, frame), reply_markup=back_menu())

@router.callback_query(F.data == "menu")
async def menu_callback(call: CallbackQuery):
    await call.message.edit_text(MENU_TEXT, reply_markup=main_menu())
    await call.answer()

@router.callback_query(F.data == "check_join")
async def check_join_button(call: CallbackQuery):
    uid = call.from_user.id
    clear_membership_cache(uid)
    if not await is_member(call.bot, uid):
        await call.answer("❌ هنوز عضو کانال نیستی. اول عضو شو و دوباره امتحان کن.", show_alert=True)
        return
    await call.answer("✅ عضویت تأیید شد!")
    try:
        await call.message.edit_text(MENU_TEXT, reply_markup=main_menu())
    except Exception:
        await call.message.answer(MENU_TEXT, reply_markup=main_menu())

@router.callback_query(F.data.in_(STATIC_KEYS))
async def section_callback(call: CallbackQuery):
    await call.message.edit_text(SECTIONS[call.data], reply_markup=back_menu())
    await call.answer()


@router.message(F.text == "/ranking")
async def ranking(message: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute(
            "SELECT user_id, first_name, username, level, points FROM users ORDER BY points DESC, level DESC LIMIT 10"
        )).fetchall()
    lines = ["🏆 <b>رتبه‌بندی روب پوینت</b>", ""]
    for i, u in enumerate(rows, 1):
        frame = await get_active_frame(u["user_id"])
        badge = f" {frame['name']}" if frame else ""
        name = u["first_name"] or (f"@{u['username']}" if u["username"] else str(u["user_id"]))
        lines.append(f"{i}. {name}{badge} — 🏅 {u['points']:,} — ⭐ {u['level']}")
    await message.answer("\n".join(lines) if rows else "هنوز کاربری ثبت نشده.", reply_markup=back_menu())
