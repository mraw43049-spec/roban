import aiosqlite
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
 user_id INTEGER PRIMARY KEY,
 username TEXT DEFAULT '',
 first_name TEXT DEFAULT '',
 coins INTEGER DEFAULT 500,
 points INTEGER DEFAULT 0,
 level INTEGER DEFAULT 1,
 xp INTEGER DEFAULT 0,
 hearts INTEGER DEFAULT 3,
 last_daily INTEGER DEFAULT 0,
 loan INTEGER DEFAULT 0,
 created_at INTEGER DEFAULT (strftime('%s','now'))
);
"""

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()

async def ensure_user(user):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users(user_id,username,first_name) VALUES(?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET username=excluded.username,first_name=excluded.first_name""",
            (user.id, user.username or "", user.first_name or "")
        )
        await db.commit()

async def get_user(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        return await (await db.execute("SELECT * FROM users WHERE user_id=?", (uid,))).fetchone()

async def change_coins(uid, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET coins=coins+? WHERE user_id=?", (amount, uid))
        await db.commit()

async def update_xp(uid, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET xp=xp+? WHERE user_id=?", (amount, uid))
        await db.execute("UPDATE users SET level=1+CAST(xp/100 AS INTEGER) WHERE user_id=?", (uid,))
        await db.commit()

async def set_daily(uid, ts, reward):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET last_daily=?,coins=coins+? WHERE user_id=?", (ts,reward,uid))
        await db.commit()

async def transfer(sender, receiver, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("BEGIN IMMEDIATE")
        a = await (await db.execute("SELECT coins FROM users WHERE user_id=?", (sender,))).fetchone()
        b = await (await db.execute("SELECT user_id FROM users WHERE user_id=?", (receiver,))).fetchone()
        if not a or not b or amount <= 0 or a[0] < amount:
            await db.rollback()
            return False
        await db.execute("UPDATE users SET coins=coins-? WHERE user_id=?", (amount,sender))
        await db.execute("UPDATE users SET coins=coins+? WHERE user_id=?", (amount,receiver))
        await db.commit()
        return True
