from decimal import Decimal, getcontext, InvalidOperation
from services import repository
from typing import Tuple, Optional


def convert(amount: Decimal, base: str, quote: str, pivot: str = "USD") -> Tuple[Decimal, Decimal, str]:
    """
    Returns (result, rate_used, method)
    method: 'direct', 'inverse', 'cross'
    """
    base = base.upper()
    quote = quote.upper()
    pivot = pivot.upper()

    if base == quote:
        return amount, Decimal("1"), "identity"

    # try direct
    r = repository.get_rate(base, quote)
    if r:
        rate = Decimal(r.rate)
        return (amount * rate, rate, "direct")

    # try inverse
    inv = repository.get_rate(quote, base)
    if inv:
        rate = Decimal("1") / Decimal(inv.rate)
        return (amount * rate, rate, "inverse")

    # try cross via pivot
    if pivot and pivot != base and pivot != quote:
        r1 = repository.get_rate(base, pivot)
        r2 = repository.get_rate(pivot, quote)
        # handle inverse possibilities
        if not r1:
            inv1 = repository.get_rate(pivot, base)
            if inv1:
                r1_rate = Decimal("1") / Decimal(inv1.rate)
            else:
                r1_rate = None
        else:
            r1_rate = Decimal(r1.rate)

        if not r2:
            inv2 = repository.get_rate(quote, pivot)
            if inv2:
                r2_rate = Decimal("1") / Decimal(inv2.rate)
            else:
                r2_rate = None
        else:
            r2_rate = Decimal(r2.rate)

        if r1_rate is not None and r2_rate is not None:
            rate = r1_rate * r2_rate
            return (amount * rate, rate, f"cross via {pivot}")

    raise ValueError("No available rate for requested conversion")
