"""Data-quality flags for daily bars.

Flags rows that are suspicious as data (zero volume, stale flat prices, closes
beyond the price limit in force, prices off the tick grid) so that later steps
can exclude them instead of silently adjusting them.

``board`` applies to every row. Per-ticker board membership isn't known yet, so
a watchlist-board stock checked with regular limits can be flagged wrongly.

Row D only uses data dated D or earlier (the previous close of the same ticker).
Flags are nullable booleans; NA means "cannot tell" (no previous bar, volume
unknown, or the date/price lies outside the loaded tables).
"""
from __future__ import annotations

from datetime import date
from functools import lru_cache

import pandas as pd

from ._load import BOARDS
from ._query import price_limits
from .bars import PRICES, validate_bars
from .ticks import tick_size

QUALITY_FLAGS: tuple[str, ...] = ("zero_volume", "stale_price", "beyond_limit", "off_tick")
_TOL = 1e-9


@lru_cache(maxsize=65536)
def _limit_band(day: date, prev_close: float, board: str) -> tuple[float, float] | None:
    """(highest, lowest) close tolerated after a previous close, or None outside the tables."""
    try:
        lim = price_limits(day, prev_close, board)
        upper, lower = lim.upper(prev_close), lim.lower(prev_close)
        return upper + tick_size(day, upper), lower - tick_size(day, max(lower, 1))
    except ValueError:
        return None


@lru_cache(maxsize=65536)
def _off_tick(day: date, close: float):
    try:
        tick = tick_size(day, close)
    except ValueError:
        return pd.NA
    rem = close % tick
    return min(rem, tick - rem) > _TOL


def quality_flags(bars: pd.DataFrame, board: str = "regular") -> pd.DataFrame:
    """Columns: date, ticker, then one nullable "boolean" column per flag, in QUALITY_FLAGS order.

    Same rows and order as ``validate_bars(bars)``; the input is not modified.
    """
    if board not in BOARDS:
        raise ValueError(f"unknown board {board!r}; use {sorted(BOARDS)}")
    df = validate_bars(bars)
    prev = df.groupby("ticker", sort=False)["close"].shift(1)

    zero = (df["volume"] == 0).astype("boolean").mask(df["volume"].isna(), pd.NA)

    flat = df[PRICES].nunique(axis=1) == 1
    stale = (flat & (df["close"] == prev)).astype("boolean").mask(prev.isna(), pd.NA)

    beyond, off = [], []
    for ts, close, pc in zip(df["date"], df["close"], prev):
        day = ts.date()
        off.append(_off_tick(day, float(close)))
        band = None if pd.isna(pc) else _limit_band(day, float(pc), board)
        beyond.append(pd.NA if band is None else bool(close > band[0] or close < band[1]))

    out = df[["date", "ticker"]].copy()
    out["zero_volume"] = zero
    out["stale_price"] = stale
    out["beyond_limit"] = pd.array(beyond, dtype="boolean")
    out["off_tick"] = pd.array(off, dtype="boolean")
    return out.reset_index(drop=True)


def quality_summary(flags: pd.DataFrame) -> pd.DataFrame:
    """Index = flag name. Columns: n_true, n_na, share_true (of non-NA rows; NaN if all NA), n_tickers."""
    rows = {}
    for name in QUALITY_FLAGS:
        col = flags[name].astype("boolean")
        n_true = int(col.fillna(False).sum())
        n_na = int(col.isna().sum())
        known = len(col) - n_na
        rows[name] = {
            "n_true": n_true,
            "n_na": n_na,
            "share_true": n_true / known if known else float("nan"),
            "n_tickers": int(flags.loc[col.fillna(False).astype(bool), "ticker"].nunique()),
        }
    out = pd.DataFrame.from_dict(rows, orient="index")
    return out.astype({"n_true": "int64", "n_na": "int64", "share_true": "float64", "n_tickers": "int64"})
