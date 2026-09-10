
import asyncio
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from db import get_user, change_points, update_xp, mission_progress
from keyboards import back_menu

router = Router()

MIN_LEVEL = 2
GROUP_TYPES = ("group", "supergroup")

GAMES = {
    "xo":         {"name": "بازی روبی XO",              "emoji": "#️⃣", "min": 2, "max": 2},
    "rps":        {"name": "بازی روبی سنگ کاغذ قیچی",   "emoji": "✊", "min": 2, "max": 2},
    "dart":       {"name": "بازی روبی دارت",             "emoji": "🎯", "min": 2, "max": 4},
    "basketball": {"name": "بازی روبی بسکتبال",          "emoji": "🏀", "min": 2, "max": 3},
    "bowling":    {"name": "بازی روبی بولینگ",           "emoji": "🎳", "min": 2, "max": 4},
}
DICE_EMOJI = {"dart": "🎯", "basketball": "🏀", "bowling": "🎳"}
CHOICE_LABEL = {"rock": "🪨 سنگ", "paper": "📄 کاغذ", "scissors": "✂️ قیچی"}
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}

lobbies = {}          # chat_id -> lobby dict
awaiting_bet = {}      # (chat_id, uid) -> game_key


def games_menu_kb():
    rows = [[InlineKeyboardButton(text=f"{g['emoji']} {g['name']}", callback_data=f"rg_new:{key}")] for key, g in GAMES.items()]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def lobby_kb(chat_id):
    lobby = lobbies[chat_id]
    game = GAMES[lobby["game"]]
    n = len(lobby["players"])
    rows = [[InlineKeyboardButton(text=f"➕ ورود به بازی ({n}/{game['max']})", callback_data="rg_join")]]
    if n >= game["min"]:
        rows.append([InlineKeyboardButton(text="▶️ شروع بازی", callback_data="rg_start")])
    rows.append([InlineKeyboardButton(text="❌ لغو بازی", callback_data="rg_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def lobby_text(chat_id):
    lobby = lobbies[chat_id]
    game = GAMES[lobby["game"]]
    players_list = "\n".join(f"• {n}" for n in lobby["names"]) or "—"
    return (
        f"{game['emoji']} <b>{game['name']}</b> 🦊\n\n"
        f"💰 مبلغ شرط هر نفر: {lobby['bet']} روب پوینت\n"
        f"👥 بازیکنا ({len(lobby['players'])}/{game['max']}):\n{players_list}\n\n"
        f"حداقل بازیکن لازم: {game['min']}"
    )


# ---------- منوی بازی‌ها ----------
@router.message(F.text.in_({"بازی روبی", "بازی های روبی", "بازی‌های روبی"}))
async def show_games_menu(message: Message):
    if message.chat.type not in GROUP_TYPES:
        await message.answer("🦊 بازی‌های روبی فقط داخل گروه قابل اجرا هستن.")
        return
    u = await get_user(message.from_user.id)
    if u["level"] < MIN_LEVEL:
        await message.answer(f"🔒 بازی‌های روبی از لول {MIN_LEVEL} به بعد باز میشن.")
        return
    lines = []
    for g in GAMES.values():
        rng = f"{g['min']}" if g["min"] == g["max"] else f"{g['min']} - {g['max']}"
        lines.append(f"{g['emoji']} {g['name']}\n└ محدودیت بازیکن: {rng} پیشی")
    text = "🐾 <b>بازی‌های روبی</b> 🦊\n\nلطفا بازی مورد نظر را انتخاب کنید ⬇\n\n" + "\n\n".join(lines)
    await message.answer(text, reply_markup=games_menu_kb())


# ---------- ساخت لابی ----------
@router.callback_query(F.data.startswith("rg_new:"))
async def rg_new(call: CallbackQuery):
    key = call.data.split(":")[1]
    game = GAMES[key]
    chat_id = call.message.chat.id
    uid = call.from_user.id

    u = await get_user(uid)
    if u["level"] < MIN_LEVEL:
        await call.answer(f"🔒 از لول {MIN_LEVEL} به بعد باز میشه.", show_alert=True)
        return
    if chat_id in lobbies:
        await call.answer("⚠️ یک بازی روبی دیگه همین الان تو این گروه در جریانه.", show_alert=True)
        return

    awaiting_bet[(chat_id, uid)] = key
    await call.message.answer(
        f"{game['emoji']} <b>{game['name']}</b>\n\n💰 مبلغ شرط رو به روب پوینت بفرست (فقط عدد):"
    )
    await call.answer()


@router.message(F.text.func(lambda t: (t or "").strip().isdigit()))
async def rg_bet_amount(message: Message):
    if message.chat.type not in GROUP_TYPES:
        return
    key_ = (message.chat.id, message.from_user.id)
    if key_ not in awaiting_bet:
        return

    amount = int(message.text.strip())
    if amount <= 0:
        await message.answer("❌ مبلغ باید بزرگ‌تر از صفر باشه. دوباره بفرست:")
        return

    u = await get_user(message.from_user.id)
    if u["points"] < amount:
        await message.answer("💸 به این اندازه روب پوینت نداری. یه مبلغ کمتر بفرست:")
        return

    game_key = awaiting_bet.pop(key_)
    chat_id = message.chat.id
    if chat_id in lobbies:
        await message.answer("⚠️ یک بازی دیگه همین الان تو این گروه در جریانه.")
        return

    await change_points(message.from_user.id, -amount)
    lobbies[chat_id] = {
        "game": game_key,
        "bet": amount,
        "creator": message.from_user.id,
        "players": [message.from_user.id],
        "names": [message.from_user.full_name],
    }
    await message.answer(lobby_text(chat_id), reply_markup=lobby_kb(chat_id))


# ---------- ورود / شروع / لغو ----------
@router.callback_query(F.data == "rg_join")
async def rg_join(call: CallbackQuery):
    chat_id = call.message.chat.id
    uid = call.from_user.id
    lobby = lobbies.get(chat_id)
    if not lobby:
        await call.answer("⌛ این بازی دیگه فعال نیست.", show_alert=True)
        return
    if uid in lobby["players"]:
        await call.answer("قبلاً وارد شدی.", show_alert=True)
        return
    game = GAMES[lobby["game"]]
    if len(lobby["players"]) >= game["max"]:
        await call.answer("ظرفیت بازی پره.", show_alert=True)
        return

    u = await get_user(uid)
    if u["level"] < MIN_LEVEL:
        await call.answer(f"🔒 از لول {MIN_LEVEL} به بعد باز میشه.", show_alert=True)
        return
    if u["points"] < lobby["bet"]:
        await call.answer("💸 روب پوینت کافی نداری.", show_alert=True)
        return

    await change_points(uid, -lobby["bet"])
    lobby["players"].append(uid)
    lobby["names"].append(call.from_user.full_name)

    if len(lobby["players"]) == game["max"]:
        await call.answer("✅ وارد بازی شدی! ظرفیت تکمیل شد، بازی شروع میشه.")
        await call.message.edit_text(lobby_text(chat_id))
        await start_game(call.message, chat_id)
    else:
        await call.message.edit_text(lobby_text(chat_id), reply_markup=lobby_kb(chat_id))
        await call.answer("✅ وارد بازی شدی!")


@router.callback_query(F.data == "rg_start")
async def rg_start(call: CallbackQuery):
    chat_id = call.message.chat.id
    lobby = lobbies.get(chat_id)
    if not lobby:
        await call.answer("⌛ این بازی دیگه فعال نیست.", show_alert=True)
        return
    if call.from_user.id != lobby["creator"]:
        await call.answer("فقط سازنده بازی می‌تونه شروع کنه.", show_alert=True)
        return
    if len(lobby["players"]) < GAMES[lobby["game"]]["min"]:
        await call.answer("بازیکن کافی نیست.", show_alert=True)
        return
    await call.answer()
    await start_game(call.message, chat_id)


@router.callback_query(F.data == "rg_cancel")
async def rg_cancel(call: CallbackQuery):
    chat_id = call.message.chat.id
    lobby = lobbies.get(chat_id)
    if not lobby:
        await call.answer()
        return
    if call.from_user.id != lobby["creator"]:
        await call.answer("فقط سازنده می‌تونه لغو کنه.", show_alert=True)
        return
    for pid in lobby["players"]:
        await change_points(pid, lobby["bet"])
    lobbies.pop(chat_id, None)
    await call.message.edit_text("❌ بازی لغو شد و مبلغ شرط‌ها برگشت داده شد.")
    await call.answer()


# ---------- شروع بازی بر اساس نوع ----------
async def start_game(message, chat_id):
    key = lobbies[chat_id]["game"]
    if key in DICE_EMOJI:
        await run_dice_game(message, chat_id)
    elif key == "rps":
        await start_rps(message, chat_id)
    elif key == "xo":
        await start_xo(message, chat_id)


async def payout(chat_id, winner_ids, refund_all=False):
    lobby = lobbies[chat_id]
    bet = lobby["bet"]
    pot = bet * len(lobby["players"])
    if refund_all:
        for pid in lobby["players"]:
            await change_points(pid, bet)
    else:
        share = pot // max(1, len(winner_ids))
        for pid in winner_ids:
            await change_points(pid, share)
    for pid in lobby["players"]:
        await update_xp(pid, 10)
        await mission_progress(pid, "game", 1, 1)
    lobbies.pop(chat_id, None)


# ---------- دارت / بسکتبال / بولینگ ----------
async def run_dice_game(message, chat_id):
    lobby = lobbies[chat_id]
    emoji = DICE_EMOJI[lobby["game"]]
    results = {}
    for uid in lobby["players"]:
        dmsg = await message.bot.send_dice(chat_id, emoji=emoji)
        await asyncio.sleep(2.5)
        results[uid] = dmsg.dice.value

    contenders = list(results.items())
    attempts = 0
    while attempts < 3:
        maxval = max(v for _, v in contenders)
        top = [uid for uid, v in contenders if v == maxval]
        if len(top) == 1:
            break
        new_results = []
        for uid in top:
            dmsg = await message.bot.send_dice(chat_id, emoji=emoji)
            await asyncio.sleep(2.5)
            new_results.append((uid, dmsg.dice.value))
        contenders = new_results
        attempts += 1

    maxval = max(v for _, v in contenders)
    winners = [uid for uid, v in contenders if v == maxval]

    lines = "\n".join(f"• {lobby['names'][lobby['players'].index(uid)]}: {val}" for uid, val in results.items())
    pot = lobby["bet"] * len(lobby["players"])
    if len(winners) == 1:
        wname = lobby["names"][lobby["players"].index(winners[0])]
        text = f"🏁 نتایج:\n{lines}\n\n🏆 برنده: {wname}\n💰 +{pot} روب پوینت 🦊"
    else:
        wnames = ", ".join(lobby["names"][lobby["players"].index(w)] for w in winners)
        text = f"🏁 نتایج:\n{lines}\n\n🤝 مساوی بین: {wnames}\n💰 پات به‌طور مساوی تقسیم شد."

    await payout(chat_id, winners, refund_all=False)
    await message.answer(text)


# ---------- سنگ کاغذ قیچی ----------
def rps_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🪨 سنگ", callback_data="rps_choice:rock"),
        InlineKeyboardButton(text="📄 کاغذ", callback_data="rps_choice:paper"),
        InlineKeyboardButton(text="✂️ قیچی", callback_data="rps_choice:scissors"),
    ]])


async def start_rps(message, chat_id):
    lobby = lobbies[chat_id]
    lobby["choices"] = {}
    names = ", ".join(lobby["names"])
    await message.answer(
        f"✊ <b>سنگ کاغذ قیچی</b> شروع شد!\n👥 {names}\n\nهر بازیکن یکی از گزینه‌ها رو مخفیانه انتخاب کنه 👇",
        reply_markup=rps_kb()
    )


@router.callback_query(F.data.startswith("rps_choice:"))
async def rps_choice(call: CallbackQuery):
    chat_id = call.message.chat.id
    lobby = lobbies.get(chat_id)
    if not lobby or lobby.get("game") != "rps" or call.from_user.id not in lobby["players"]:
        await call.answer()
        return
    uid = call.from_user.id
    if uid in lobby["choices"]:
        await call.answer("قبلاً انتخاب کردی.", show_alert=True)
        return
    choice = call.data.split(":")[1]
    lobby["choices"][uid] = choice
    await call.answer(f"انتخابت ثبت شد: {CHOICE_LABEL[choice]}")
    if len(lobby["choices"]) == len(lobby["players"]):
        await resolve_rps(call.message, chat_id)


async def resolve_rps(message, chat_id):
    lobby = lobbies[chat_id]
    p1, p2 = lobby["players"][0], lobby["players"][1]
    c1, c2 = lobby["choices"][p1], lobby["choices"][p2]
    n1, n2 = lobby["names"][0], lobby["names"][1]

    reveal = f"👤 {n1}: {CHOICE_LABEL[c1]}\n👤 {n2}: {CHOICE_LABEL[c2]}"

    if c1 == c2:
        await payout(chat_id, [], refund_all=True)
        await message.answer(f"✊ نتیجه:\n{reveal}\n\n🤝 مساوی شد! مبلغ شرط برگشت داده شد.")
        return

    winner = p1 if BEATS[c1] == c2 else p2
    wname = n1 if winner == p1 else n2
    pot = lobby["bet"] * 2
    await payout(chat_id, [winner], refund_all=False)
    await message.answer(f"✊ نتیجه:\n{reveal}\n\n🏆 برنده: {wname}\n💰 +{pot} روب پوینت 🦊")


# ---------- XO دو نفره ----------
def rg_ttt_kb(board):
    rows = []
    for r in range(3):
        row = []
        for c in range(3):
            i = r * 3 + c
            row.append(InlineKeyboardButton(text=board[i] or "▫️", callback_data=f"rttt:{i}"))
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ttt_winner(b):
    lines = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))
    for a, c, d in lines:
        if b[a] and b[a] == b[c] == b[d]:
            return b[a]
    return "draw" if all(b) else None


def xo_render(board):
    return "\n".join(" | ".join(board[i:i + 3][j] or "▫️" for j in range(3)) for i in range(0, 9, 3))


def xo_text(chat_id):
    lobby = lobbies[chat_id]
    turn_name = lobby["names"][lobby["players"].index(lobby["turn"])]
    symbol = "❌" if lobby["turn"] == lobby["players"][0] else "⭕"
    return (
        f"#️⃣ <b>بازی روبی XO</b> 🦊\n\n"
        f"❌ {lobby['names'][0]}   |   ⭕ {lobby['names'][1]}\n\n"
        f"نوبت: {turn_name} ({symbol})"
    )


async def start_xo(message, chat_id):
    lobby = lobbies[chat_id]
    lobby["board"] = [""] * 9
    lobby["turn"] = lobby["players"][0]
    await message.answer(xo_text(chat_id), reply_markup=rg_ttt_kb(lobby["board"]))


@router.callback_query(F.data.startswith("rttt:"))
async def rg_ttt_move(call: CallbackQuery):
    chat_id = call.message.chat.id
    lobby = lobbies.get(chat_id)
    if not lobby or lobby.get("game") != "xo" or "board" not in lobby:
        await call.answer()
        return
    uid = call.from_user.id
    if uid != lobby["turn"]:
        await call.answer("نوبت تو نیست.", show_alert=True)
        return

    idx = int(call.data.split(":")[1])
    board = lobby["board"]
    if board[idx]:
        await call.answer("این خونه پره.", show_alert=True)
        return

    symbol = "❌" if uid == lobby["players"][0] else "⭕"
    board[idx] = symbol
    result = ttt_winner(board)

    if result is None:
        lobby["turn"] = lobby["players"][1] if uid == lobby["players"][0] else lobby["players"][0]
        await call.message.edit_text(xo_text(chat_id), reply_markup=rg_ttt_kb(board))
        await call.answer()
        return

    await call.answer()
    pot = lobby["bet"] * 2
    if result == "draw":
        await call.message.edit_text(f"#️⃣ <b>بازی روبی XO</b> 🦊\n\n🤝 مساوی شد! مبلغ شرط برگشت داده شد.")
        await payout(chat_id, [], refund_all=True)
        return

    winner_uid = lobby["players"][0] if result == "❌" else lobby["players"][1]
    wname = lobby["names"][0] if result == "❌" else lobby["names"][1]
    await call.message.edit_text(f"#️⃣ <b>بازی روبی XO</b> 🦊\n\n🏆 برنده: {wname}\n💰 +{pot} روب پوینت 🦊")
    await payout(chat_id, [winner_uid], refund_all=False)
