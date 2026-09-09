# Gorbaw Telegram Bot — Railway-ready

This version is intentionally **flat**: it does not import an `app` package, so it avoids `ModuleNotFoundError: No module named 'app'` when deployed on Railway.

## Railway settings
- Root Directory: **empty** (repository root)
- Start Command: `python main.py`
- Variable: `BOT_TOKEN` = your Telegram bot token
- Optional: `ADMIN_IDS` = comma-separated Telegram user IDs
- Optional: `DB_PATH` = `/data/gorbaw.sqlite3` if a persistent volume is mounted; otherwise the bot falls back to `gorbaw.sqlite3`.

## GitHub
Upload/commit **all files and folders in this ZIP** to the repository root. Do not upload only `main.py`.

Never put your real `BOT_TOKEN` in GitHub.
