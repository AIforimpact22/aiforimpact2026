from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class Currency:
    code: str
    name: str
    symbol: Optional[str] = None
    active: bool = True


@dataclass
class Rate:
    base_currency: str
    quote_currency: str
    rate: Decimal
    effective_date: str


@dataclass
class ConversionRecord:
    timestamp: str
    base_currency: str
    quote_currency: str
    amount: Decimal
    result: Decimal
    rate_used: Decimal
    method: str
