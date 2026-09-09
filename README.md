# Gorbaw Telegram Bot — Railway-ready v2

This version keeps the original Railway structure and turns the main menu into working bot flows.

## Implemented
- User registration, profile, XP and levels
- Daily reward and mission progress/claim
- Coin balance and atomic user-to-user transfer
- Virtual Ruby Point purchases
- Market packages
- Factory production and upgrades
- Virtual bank loan and repayment
- Wheel of chance using virtual coins only
- Dice and playable single-player Tic-Tac-Toe
- Fun football simulation using virtual XP only
- Virtual inventory / insect collection
- Raffle entry flow (free, virtual)
- Pairing/production flow
- Admin coin management and user lookup
- Frame shop foundation: buy once, permanent ownership, activate/deactivate

## Frames
Frame records are seeded in the database with placeholder asset paths:
- frames/fire.gif
- frames/royal.gif
- frames/lightning.gif

Replace these placeholders with the actual frame assets later. The ownership/active-state database logic is already in place.

## Railway
- Root Directory: repository root
- Start Command: `python main.py`
- `BOT_TOKEN` is required
- `ADMIN_IDS` is optional and accepts comma-separated Telegram user IDs
- `DB_PATH` can be `/data/gorbaw.sqlite3` when a persistent Railway volume is mounted

Never commit a real `BOT_TOKEN` to GitHub.
