import aiosqlite

DB_PATH = "smm_bot.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id   INTEGER PRIMARY KEY,
                balance   INTEGER NOT NULL DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                service_type TEXT    NOT NULL,
                amount       INTEGER NOT NULL,
                price        INTEGER NOT NULL,
                link         TEXT,
                status       TEXT    NOT NULL DEFAULT 'В обработке'
            )
        """)
        await db.commit()


# ── Users ──────────────────────────────────────────────────────────────────

async def get_or_create_user(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,)
        )
        await db.commit()
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row)


async def get_balance(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT balance FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


async def add_balance(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id),
        )
        await db.commit()


async def deduct_balance(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance - ? WHERE user_id = ?",
            (amount, user_id),
        )
        await db.commit()


# ── Orders ─────────────────────────────────────────────────────────────────

async def create_order(user_id: int, service_type: str, amount: int, price: int) -> int:
    """Creates order WITHOUT link yet. Returns order_id."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO orders (user_id, service_type, amount, price)
               VALUES (?, ?, ?, ?)""",
            (user_id, service_type, amount, price),
        )
        await db.commit()
        return cur.lastrowid


async def set_order_link(order_id: int, link: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE orders SET link = ? WHERE order_id = ?", (link, order_id)
        )
        await db.commit()


async def set_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id)
        )
        await db.commit()


async def get_order(order_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE order_id = ?", (order_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_all_orders() -> list[dict]:
    """Returns all orders."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders ORDER BY order_id DESC"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

async def get_user_orders(user_id: int) -> list[dict]:
    """Returns all orders for specific user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY order_id DESC", (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT COUNT(*) FROM orders WHERE status = 'В обработке'"
        ) as cur:
            pending = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT COUNT(*) FROM orders WHERE status = 'Выполнено'"
        ) as cur:
            done = (await cur.fetchone())[0]
        return {"total_users": total_users, "pending": pending, "done": done}