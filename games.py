
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from db import update_xp, mission_progress
from keyboards import back_menu, ttt_kb

router = Router()
boards = {}

def render_board(board):
    return "\n".join(" | ".join(board[i:i+3]) for i in range(0,9,3))

@router.callback_query(F.data == "dice")
async def dice_button(call: CallbackQuery):
    n=random.randint(1,6)
    await update_xp(call.from_user.id,5)
    await mission_progress(call.from_user.id,"game",1,1)
    await call.message.answer(f"🎲 تاس: <b>{n}</b>\n✨ +5 XP", reply_markup=back_menu())
    await call.answer()

@router.message(F.text == "/dice")
async def dice_cmd(message: Message):
    n=random.randint(1,6)
    await update_xp(message.from_user.id,5)
    await mission_progress(message.from_user.id,"game",1,1)
    await message.answer(f"🎲 تاس: <b>{n}</b>\n✨ +5 XP", reply_markup=back_menu())

@router.callback_query(F.data == "tictactoe")
async def ttt_button(call: CallbackQuery):
    boards[call.from_user.id] = [""] * 9
    await call.message.answer("⌗ <b>بازی دوز</b>\n\nتو با ❌ بازی می‌کنی؛ ربات با ⭕.", reply_markup=ttt_kb(boards[call.from_user.id]))
    await call.answer()

def winner(b):
    lines=((0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6))
    for a,c,d in lines:
        if b[a] and b[a]==b[c]==b[d]:
            return b[a]
    return "draw" if all(b) else None

def bot_move(b):
    free=[i for i,v in enumerate(b) if not v]
    if not free: return
    # Win if possible
    for i in free:
        b[i]="⭕"
        if winner(b)=="⭕": return
        b[i]=""
    # Block player
    for i in free:
        b[i]="❌"
        if winner(b)=="❌":
            b[i]="⭕"
            return
        b[i]=""
    b[random.choice(free)]="⭕"

@router.message(F.text == "/tictactoe")
async def ttt(message: Message):
    boards[message.from_user.id] = [""] * 9
    await message.answer("⌗ <b>بازی دوز</b>\n\nتو با ❌ بازی می‌کنی؛ ربات با ⭕.", reply_markup=ttt_kb(boards[message.from_user.id]))

@router.callback_query(F.data.startswith("ttt:"))
async def ttt_move(call: CallbackQuery):
    uid=call.from_user.id
    b=boards.get(uid)
    if b is None:
        b=[""]*9
        boards[uid]=b
    idx=int(call.data.split(":")[1])
    if idx<0 or idx>8 or b[idx]:
        await call.answer("این خانه خالی نیست.", show_alert=True)
        return
    b[idx]="❌"
    result=winner(b)
    if result is None:
        bot_move(b)
        result=winner(b)
    if result:
        if result=="❌":
            msg="🎉 بردی!"
            await update_xp(uid,20)
        elif result=="⭕":
            msg="🤖 ربات برد."
            await update_xp(uid,5)
        else:
            msg="🤝 مساوی شد."
            await update_xp(uid,10)
        await mission_progress(uid,"game",1,1)
        boards.pop(uid,None)
        await call.message.edit_text(f"⌗ <b>بازی دوز</b>\n\n{render_board(b)}\n\n{msg}\n✨ XP ثبت شد.", reply_markup=back_menu())
    else:
        await call.message.edit_reply_markup(reply_markup=ttt_kb(b))
    await call.answer()
