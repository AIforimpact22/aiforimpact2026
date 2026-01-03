from decimal import Decimal
from typing import List, Optional
import db
from models import Currency, Rate, ConversionRecord
from datetime import datetime


def list_currencies(active_only: bool = False) -> List[Currency]:
    conn = db.get_conn()
    cur = conn.cursor()
    if active_only:
        cur.execute("SELECT code,name,symbol,active FROM currencies WHERE active=1 ORDER BY code")
    else:
        cur.execute("SELECT code,name,symbol,active FROM currencies ORDER BY code")
    rows = cur.fetchall()
    conn.close()
    return [Currency(row[0], row[1], row[2], bool(row[3])) for row in rows]


def get_currency(code: str) -> Optional[Currency]:
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT code,name,symbol,active FROM currencies WHERE code=?", (code.upper(),))
    row = cur.fetchone()
    conn.close()
    if row:
        return Currency(row[0], row[1], row[2], bool(row[3]))
    return None


def upsert_currency(code: str, name: str, symbol: str = None, active: bool = True):
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO currencies(code,name,symbol,active) VALUES (?, ?, ?, ?)",
        (code.upper(), name, symbol, 1 if active else 0),
    )
    conn.commit()
    conn.close()


def delete_currency(code: str):
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM currencies WHERE code=?", (code.upper(),))
    conn.commit()
    conn.close()


def list_rates() -> List[Rate]:
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT base_currency,quote_currency,rate,effective_date FROM rates ORDER BY base_currency, quote_currency")
    rows = cur.fetchall()
    conn.close()
    return [Rate(r[0], r[1], Decimal(r[2]), r[3]) for r in rows]


def upsert_rate(base: str, quote: str, rate: Decimal, effective_date: str):
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO rates(base_currency,quote_currency,rate,effective_date) VALUES (?, ?, ?, ?)",
        (base.upper(), quote.upper(), str(rate), effective_date),
    )
    conn.commit()
    conn.close()


def delete_rate(base: str, quote: str):
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM rates WHERE base_currency=? AND quote_currency=?", (base.upper(), quote.upper()))
    conn.commit()
    conn.close()


def get_rate(base: str, quote: str) -> Optional[Rate]:
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT base_currency,quote_currency,rate,effective_date FROM rates WHERE base_currency=? AND quote_currency=?",
        (base.upper(), quote.upper()),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return Rate(row[0], row[1], Decimal(row[2]), row[3])
    return None


def log_conversion(base: str, quote: str, amount: Decimal, result: Decimal, rate_used: Decimal, method: str):
    ts = datetime.utcnow().isoformat()
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO history(timestamp,base_currency,quote_currency,amount,result,rate_used,method) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (ts, base.upper(), quote.upper(), str(amount), str(result), str(rate_used), method),
    )
    conn.commit()
    conn.close()
    db.prune_history(50)


def get_history(limit: int = 50):
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT timestamp,base_currency,quote_currency,amount,result,rate_used,method FROM history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [ConversionRecord(r[0], r[1], r[2], Decimal(r[3]), Decimal(r[4]), Decimal(r[5]), r[6]) for r in rows]
