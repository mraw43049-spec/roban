
import aiosqlite
import time
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
 loan_due INTEGER DEFAULT 0,
 factory_level INTEGER DEFAULT 1,
 factory_last INTEGER DEFAULT 0,
 last_hoohoo INTEGER DEFAULT 0,
 hoohoo_count INTEGER DEFAULT 0,
 last_hunt INTEGER DEFAULT 0,
 created_at INTEGER DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS inventory(
 user_id INTEGER NOT NULL,
 item TEXT NOT NULL,
 quantity INTEGER DEFAULT 0,
 PRIMARY KEY(user_id,item)
);

CREATE TABLE IF NOT EXISTS frames(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL UNIQUE,
 price INTEGER NOT NULL DEFAULT 0,
 asset TEXT DEFAULT '',
 active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS user_frames(
 user_id INTEGER NOT NULL,
 frame_id INTEGER NOT NULL,
 active INTEGER DEFAULT 0,
 purchased_at INTEGER DEFAULT (strftime('%s','now')),
 PRIMARY KEY(user_id,frame_id)
);

CREATE TABLE IF NOT EXISTS missions(
 user_id INTEGER NOT NULL,
 mission TEXT NOT NULL,
 progress INTEGER DEFAULT 0,
 target INTEGER DEFAULT 1,
 claimed INTEGER DEFAULT 0,
 PRIMARY KEY(user_id,mission)
);

CREATE TABLE IF NOT EXISTS raffles(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT NOT NULL,
 entry_cost INTEGER DEFAULT 0,
 prize INTEGER DEFAULT 0,
 ends_at INTEGER NOT NULL,
 winner_id INTEGER DEFAULT NULL,
 status TEXT DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS raffle_entries(
 raffle_id INTEGER NOT NULL,
 user_id INTEGER NOT NULL,
 PRIMARY KEY(raffle_id,user_id)
);
"""

DEFAULT_FRAMES = [
    ("🔥 آتش", 5000, "frames/fire.gif"),
    ("👑 سلطنتی", 10000, "frames/royal.gif"),
    ("⚡ برق", 7500, "frames/lightning.gif"),
]

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        existing = {row[1] for row in await (await db.execute("PRAGMA table_info(users)")).fetchall()}
        migrations = {
            "loan_due": "ALTER TABLE users ADD COLUMN loan_due INTEGER DEFAULT 0",
            "factory_level": "ALTER TABLE users ADD COLUMN factory_level INTEGER DEFAULT 1",
            "factory_last": "ALTER TABLE users ADD COLUMN factory_last INTEGER DEFAULT 0",
            "last_hoohoo": "ALTER TABLE users ADD COLUMN last_hoohoo INTEGER DEFAULT 0",
            "hoohoo_count": "ALTER TABLE users ADD COLUMN hoohoo_count INTEGER DEFAULT 0",
            "last_hunt": "ALTER TABLE users ADD COLUMN last_hunt INTEGER DEFAULT 0",
        }
        for col, sql in migrations.items():
            if col not in existing:
                await db.execute(sql)
        await db.executemany(
            "INSERT OR IGNORE INTO frames(name,price,asset) VALUES(?,?,?)",
            DEFAULT_FRAMES
        )
        await db.commit()

async def ensure_user(user):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users(user_id,username,first_name,factory_last) VALUES(?,?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET username=excluded.username,first_name=excluded.first_name""",
            (user.id, user.username or "", user.first_name or "", int(time.time()))
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

async def spend_coins(uid, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("BEGIN IMMEDIATE")
        row = await (await db.execute("SELECT coins FROM users WHERE user_id=?", (uid,))).fetchone()
        if not row or amount < 0 or row[0] < amount:
            await db.rollback()
            return False
        await db.execute("UPDATE users SET coins=coins-? WHERE user_id=?", (amount, uid))
        await db.commit()
        return True

async def change_points(uid, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET points=MAX(0,points+?) WHERE user_id=?", (amount, uid))
        await db.commit()

async def update_xp(uid, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET xp=MAX(0,xp+?) WHERE user_id=?", (amount, uid))
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
        if not a or not b or amount <= 0 or sender == receiver or a[0] < amount:
            await db.rollback()
            return False
        await db.execute("UPDATE users SET coins=coins-? WHERE user_id=?", (amount,sender))
        await db.execute("UPDATE users SET coins=coins+? WHERE user_id=?", (amount,receiver))
        await db.commit()
        return True


async def transfer_points(sender, receiver, amount):
    """Atomic روب پوینت transfer with a hard per-transfer limit."""
    MAX_TRANSFER = 500_000
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("BEGIN IMMEDIATE")
        a = await (await db.execute("SELECT points FROM users WHERE user_id=?", (sender,))).fetchone()
        b = await (await db.execute("SELECT user_id FROM users WHERE user_id=?", (receiver,))).fetchone()
        if not a or not b or amount <= 0 or amount > MAX_TRANSFER or sender == receiver or a[0] < amount:
            await db.rollback()
            return False, "invalid"
        await db.execute("UPDATE users SET points=points-? WHERE user_id=?", (amount, sender))
        await db.execute("UPDATE users SET points=points+? WHERE user_id=?", (amount, receiver))
        await db.commit()
        return True, "ok"

async def set_points(uid, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET points=MAX(0,?) WHERE user_id=?", (int(value), uid))
        await db.commit()

async def set_level(uid, level):
    level = max(1, int(level))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET level=? WHERE user_id=?", (level, uid))
        await db.commit()

async def get_user_ids():
    async with aiosqlite.connect(DB_PATH) as db:
        rows = await (await db.execute("SELECT user_id FROM users ORDER BY user_id")).fetchall()
        return [r[0] for r in rows]

async def bot_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        row = await (await db.execute("""
            SELECT COUNT(*), COALESCE(SUM(coins),0), COALESCE(SUM(points),0),
                   COALESCE(MAX(level),1)
            FROM users
        """)).fetchone()
        frames = (await (await db.execute("SELECT COUNT(*) FROM user_frames")).fetchone())[0]
        inventory = (await (await db.execute("SELECT COALESCE(SUM(quantity),0) FROM inventory")).fetchone())[0]
        missions = (await (await db.execute("SELECT COUNT(*) FROM missions")).fetchone())[0]
        return {
            "users": row[0], "coins": row[1], "points": row[2], "max_level": row[3],
            "frame_ownerships": frames, "inventory_items": inventory, "missions": missions
        }

async def list_frames(uid=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if uid is None:
            return await (await db.execute("SELECT * FROM frames WHERE active=1 ORDER BY id")).fetchall()
        return await (await db.execute("""
            SELECT f.*, CASE WHEN uf.frame_id IS NULL THEN 0 ELSE 1 END AS owned,
                   COALESCE(uf.active,0) AS owned_active
            FROM frames f LEFT JOIN user_frames uf
            ON uf.frame_id=f.id AND uf.user_id=?
            WHERE f.active=1 ORDER BY f.id
        """,(uid,))).fetchall()

async def buy_frame(uid, frame_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("BEGIN IMMEDIATE")
        f = await (await db.execute("SELECT id,price FROM frames WHERE id=? AND active=1",(frame_id,))).fetchone()
        owned = await (await db.execute("SELECT 1 FROM user_frames WHERE user_id=? AND frame_id=?",(uid,frame_id))).fetchone()
        u = await (await db.execute("SELECT coins FROM users WHERE user_id=?",(uid,))).fetchone()
        if not f or owned or not u or u[0] < f[1]:
            await db.rollback()
            return False, "not_allowed"
        await db.execute("UPDATE users SET coins=coins-? WHERE user_id=?",(f[1],uid))
        await db.execute("INSERT INTO user_frames(user_id,frame_id,active) VALUES(?,?,0)",(uid,frame_id))
        await db.commit()
        return True, "ok"

async def set_active_frame(uid, frame_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("BEGIN IMMEDIATE")
        owned = await (await db.execute("SELECT 1 FROM user_frames WHERE user_id=? AND frame_id=?",(uid,frame_id))).fetchone()
        if not owned:
            await db.rollback()
            return False
        await db.execute("UPDATE user_frames SET active=0 WHERE user_id=?",(uid,))
        await db.execute("UPDATE user_frames SET active=1 WHERE user_id=? AND frame_id=?",(uid,frame_id))
        await db.commit()
        return True

async def disable_frame(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE user_frames SET active=0 WHERE user_id=?",(uid,))
        await db.commit()

async def get_active_frame(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory=aiosqlite.Row
        return await (await db.execute("""
            SELECT f.* FROM frames f JOIN user_frames uf ON uf.frame_id=f.id
            WHERE uf.user_id=? AND uf.active=1 LIMIT 1
        """,(uid,))).fetchone()

async def mission_progress(uid, mission, amount=1, target=1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""INSERT INTO missions(user_id,mission,progress,target)
            VALUES(?,?,?,?) ON CONFLICT(user_id,mission) DO UPDATE SET progress=MIN(missions.target,missions.progress+?)""",
            (uid,mission,amount,target,amount))
        await db.commit()

async def get_missions(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory=aiosqlite.Row
        rows = await (await db.execute("SELECT * FROM missions WHERE user_id=? ORDER BY mission",(uid,))).fetchall()
        return rows

async def claim_mission(uid, mission, reward):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("BEGIN IMMEDIATE")
        row = await (await db.execute("SELECT progress,target,claimed FROM missions WHERE user_id=? AND mission=?",(uid,mission))).fetchone()
        if not row or row[2] or row[0] < row[1]:
            await db.rollback()
            return False
        await db.execute("UPDATE missions SET claimed=1 WHERE user_id=? AND mission=?",(uid,mission))
        await db.execute("UPDATE users SET coins=coins+? WHERE user_id=?",(reward,uid))
        await db.commit()
        return True

async def register_hoohoo(uid, ts):
    """Register a new hoohoo claim and return the total hoohoo count for the user."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET last_hoohoo=?, hoohoo_count=hoohoo_count+1 WHERE user_id=?",
            (ts, uid)
        )
        await db.commit()
        row = await (await db.execute("SELECT hoohoo_count FROM users WHERE user_id=?", (uid,))).fetchone()
        return row[0] if row else 0

async def set_hunt_time(uid, ts):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET last_hunt=? WHERE user_id=?", (ts, uid))
        await db.commit()

async def level_up_to_next(uid):
    """Bump the user exactly one level (consistent with level=1+xp//100) and return the new level."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await (await db.execute("SELECT xp, level FROM users WHERE user_id=?", (uid,))).fetchone()
        if not row:
            return None
        target_xp = row["level"] * 100
        add = target_xp - row["xp"]
        if add < 1:
            add = 100
        new_xp = row["xp"] + add
        new_level = 1 + new_xp // 100
        await db.execute("UPDATE users SET xp=?, level=? WHERE user_id=?", (new_xp, new_level, uid))
        await db.commit()
        return new_level

async def add_inventory_item(uid, item, qty=1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO inventory(user_id,item,quantity) VALUES(?,?,?)
               ON CONFLICT(user_id,item) DO UPDATE SET quantity=quantity+?""",
            (uid, item, qty, qty)
        )
        await db.commit()
