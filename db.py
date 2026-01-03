import sqlite3
from pathlib import Path
from datetime import datetime
from decimal import Decimal

DB_PATH = Path("data") / "app.db"


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
    CREATE TABLE IF NOT EXISTS currencies (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        symbol TEXT,
        active INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS rates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        base_currency TEXT NOT NULL,
        quote_currency TEXT NOT NULL,
        rate TEXT NOT NULL,
        effective_date TEXT NOT NULL,
        UNIQUE(base_currency, quote_currency) ON CONFLICT REPLACE
    );

    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        base_currency TEXT NOT NULL,
        quote_currency TEXT NOT NULL,
        amount TEXT NOT NULL,
        result TEXT NOT NULL,
        rate_used TEXT NOT NULL,
        method TEXT NOT NULL
    );
    """
    )
    conn.commit()
    conn.close()


def seed_common_currencies():
    conn = get_conn()
    cur = conn.cursor()
    common = [
        ("USD", "US Dollar", "$", 1),
        ("EUR", "Euro", "€", 1),
        ("GBP", "British Pound", "£", 1),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO currencies(code, name, symbol, active) VALUES (?, ?, ?, ?)",
        common,
    )
    conn.commit()
    conn.close()


def prune_history(limit=50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM history")
    cnt = cur.fetchone()[0]
    if cnt > limit:
        to_remove = cnt - limit
        cur.execute("DELETE FROM history WHERE id IN (SELECT id FROM history ORDER BY id ASC LIMIT ?)", (to_remove,))
        conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_common_currencies()
    print("Initialized DB and seeded currencies at", DB_PATH)
