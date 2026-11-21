"""Limit-normalised returns, ARA/ARB hit flags and ARA run length (PLAN.md 3.2, feature 1)."""
from __future__ import annotations

from datetime import date
from functools import lru_cache

import numpy as np
import pandas as pd

from .._query import price_limits
from ..bars import validate_bars
from ..ticks import round_to_tick



@lru_cache(maxsize=65536)
def _cached_limits(day: date, prev: float, board: str):
    return price_limits(day, prev, board)


@lru_cache(maxsize=65536)
def _cached_round(price: float, day: date, mode: str) -> int:
    return round_to_tick(price, day, mode)


@lru_cache(maxsize=65536)
def _limit_levels(day: date, prev: float, board: str):
    """(up/prev - 1, 1 - dn/prev, ara price, arb price), or None outside the tables."""
    try:
        lim = _cached_limits(day, prev, board)
        up, dn = lim.upper(prev), lim.lower(prev)
        return (up / prev - 1, 1 - dn / prev,
                _cached_round(up, day, "down"),
                _cached_round(dn, day, "up") if dn > 0 else 1)  # Rp1 is the minimum price
    except ValueError:
        return None


def limit_features(bars: pd.DataFrame, board: str = "regular") -> pd.DataFrame:
    """Columns: date, ticker, ret, ret_norm, ara_hit, arb_hit, ara_run (see tasks/P2-01.md)."""
    df = validate_bars(bars)
    prev = df.groupby("ticker", sort=False)["close"].shift(1)
    n = len(df)
    ret = np.full(n, np.nan)
    ret_norm = np.full(n, np.nan)
    ara = [pd.NA] * n
    arb = [pd.NA] * n

    for i, (d, p, c) in enumerate(zip(df["date"], prev, df["close"])):
        if pd.isna(p):
            continue
        p, c = float(p), float(c)
        ret[i] = c / p - 1
        levels = _limit_levels(d.date(), p, board)
        if levels is None:
            continue
        up_pct, dn_pct, ara_px, arb_px = levels
        denom = up_pct if ret[i] >= 0 else dn_pct
        ret_norm[i] = ret[i] / denom if denom != 0 else np.nan
        ara[i] = c >= ara_px
        arb[i] = c <= arb_px
    # ret is NA wherever the limit tables could not be applied, per spec
    ara_s = pd.array(ara, dtype="boolean")
    arb_s = pd.array(arb, dtype="boolean")
    ret = np.where(ara_s.isna(), np.nan, ret)

    # run length per ticker; NA resets the count
    run = [pd.NA] * n
    count: dict[str, int] = {}
    for i, (tk, h) in enumerate(zip(df["ticker"], ara_s)):
        if h is pd.NA:
            count[tk] = 0
            continue
        count[tk] = count.get(tk, 0) + 1 if h else 0
        run[i] = count[tk]

    return pd.DataFrame({
        "date": df["date"],
        "ticker": df["ticker"],
        "ret": pd.Series(ret, dtype="float64"),
        "ret_norm": pd.Series(ret_norm, dtype="float64"),
        "ara_hit": pd.Series(ara_s, dtype="boolean"),
        "arb_hit": pd.Series(arb_s, dtype="boolean"),
        "ara_run": pd.Series(run, dtype="Int64"),
    }).reset_index(drop=True)
