import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_PATH = os.getenv("DB_PATH", "/data/gorbaw.sqlite3")
if not os.path.isdir(os.path.dirname(DB_PATH)):
    DB_PATH = "gorbaw.sqlite3"

# عضویت اجباری
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "@fox_frenzy")
REQUIRED_CHANNEL_URL = os.getenv("REQUIRED_CHANNEL_URL", "https://t.me/fox_frenzy")

# مدیر اصلی + مدیرهای اضافه از متغیر محیطی
ADMIN_IDS = {7287316708}
ADMIN_IDS.update(int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit())
