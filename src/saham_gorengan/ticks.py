"""IDX tick sizes (fraksi harga) by date, and rounding to the tick grid."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from functools import lru_cache

from ._load import _rows

MODES = frozenset({"down", "up", "nearest"})


@dataclass(frozen=True)
class TickBand:
    band_id: str
    effective_from: date
    effective_to: date | None  # inclusive; None = still in force as far as the source knows
    price_gte: int
    price_lt: int | None  # None = no upper bound
    tick_idr: int
    decree: str  # may be blank when the source names none
    source_url: str
    notes: str


def _required(r: dict[str, str], field: str) -> str:
    v = (r[field] or "").strip()
    if not v:
        raise ValueError(f"{r.get('band_id') or '?'}: {field} is required")
    return v


def _band(r: dict[str, str]) -> TickBand:
    bid = _required(r, "band_id")
    try:
        start = date.fromisoformat(_required(r, "effective_from"))
        end = date.fromisoformat(r["effective_to"]) if r["effective_to"] else None
        gte = int(_required(r, "price_gte"))
        lt = int(r["price_lt"]) if r["price_lt"] else None
        tick = int(_required(r, "tick_idr"))
    except ValueError as e:
        raise ValueError(f"{bid}: bad value ({e})") from e
    if tick <= 0:
        raise ValueError(f"{bid}: tick_idr must be a positive int, got {tick}")
    if end is not None and end < start:
        raise ValueError(f"{bid}: effective_to before effective_from")
    if gte < 0 or (lt is not None and lt <= gte):
        raise ValueError(f"{bid}: bad price range [{gte}, {lt})")
    return TickBand(bid, start, end, gte, lt, tick, r["decree"], _required(r, "source_url"), r["notes"])


@lru_cache(maxsize=None)
def _bands() -> tuple[TickBand, ...]:
    return tuple(_band(r) for r in _rows("tick_sizes.csv"))


def load_tick_sizes() -> list[TickBand]:
    """One row per (period, price band)."""
    return list(_bands())


def _band_for(day: date, price: float) -> TickBand:
    if not price > 0:
        raise ValueError(f"price must be positive, got {price!r}")
    bands = _bands()
    in_force = [b for b in bands if b.effective_from <= day and (b.effective_to is None or day <= b.effective_to)]
    if not in_force:
        if day < min(b.effective_from for b in bands):
            raise ValueError(f"{day}: before tick-size coverage starts")
        raise ValueError(f"{day}: no tick-size period covers this date")
    for b in in_force:
        if b.price_gte <= price and (b.price_lt is None or price < b.price_lt):
            return b
    raise ValueError(f"{day}: no tick band covers price {price!r}")


def tick_size(day: date, price: float) -> int:
    """Tick (IDR) in force on `day` for a price of exactly `price` (lower bound inclusive)."""
    return _band_for(day, price).tick_idr


def round_to_tick(price: float, day: date, mode: str = "down") -> int:
    """Round `price` to a multiple of the tick of the input price's band.

    mode: "down", "up", or "nearest" (ties go up). Every band boundary is a multiple of
    the tick above it, so the result is also on the grid of its own band, even when
    rounding up lands exactly on the next band's lower bound.
    """
    if mode not in MODES:
        raise ValueError(f"mode={mode!r} not in {sorted(MODES)}")
    tick = tick_size(day, price)
    q = Decimal(str(price)) / tick  # decimal repr avoids float error such as 0.1 + 0.2
    if mode == "down":
        n = math.floor(q)
    elif mode == "up":
        n = math.ceil(q)
    else:
        n = math.floor(q + Decimal("0.5"))
    return int(n) * tick
