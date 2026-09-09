import os
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_PATH = os.getenv("DB_PATH", "/data/gorbaw.sqlite3")
if not os.path.isdir(os.path.dirname(DB_PATH)):
    DB_PATH = "gorbaw.sqlite3"
