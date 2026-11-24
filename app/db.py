import aiosqlite
from datetime import datetime
from .config import settings

async def init_db():
    async with aiosqlite.connect(settings.database_url) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            sub_until TEXT,
            daily_used INTEGER DEFAULT 0,
            last_reset TEXT
        )""")
        await db.commit()

async def get_user(conn, user_id):
    cur = await conn.execute("SELECT sub_until,daily_used,last_reset FROM users WHERE user_id=?", (user_id,))
    return await cur.fetchone()

async def reserve_daily_quota(conn, user_id, duration):
    now = datetime.utcnow()
    async with conn.execute("BEGIN IMMEDIATE"):
        pass
    try:
        row = await get_user(conn, user_id)
        sub_until, used, last_reset = row or (None, 0, None)
        if sub_until and datetime.fromisoformat(sub_until) > now:
            return True
        if not last_reset or datetime.fromisoformat(last_reset).date() != now.date():
            used = 0
        if used + duration > settings.free_quota:
            return False
        await conn.execute(
            """
            INSERT INTO users(user_id, daily_used, last_reset) VALUES(?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                daily_used=excluded.daily_used, last_reset=excluded.last_reset
            """,
            (user_id, used + duration, now.isoformat()),
        )
        await conn.commit()
        return True
    finally:
        if conn.in_transaction:
            await conn.rollback()

async def add_or_update_user(conn, user_id, sub_until=None):
    await conn.execute("""
        INSERT INTO users(user_id, sub_until, daily_used, last_reset)
        VALUES(?,?,0,?)
        ON CONFLICT(user_id) DO UPDATE SET sub_until=excluded.sub_until
    """, (user_id, sub_until, datetime.utcnow().isoformat()))
    await conn.commit()
