"""Market-adjusted abnormal returns against a leave-one-out equal-weighted panel (PLAN.md 3.2, feature 2)."""
from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd

from ..bars import validate_bars


def _check_horizons(horizons: Sequence[int]) -> list[int]:
    hs = list(horizons)
    for h in hs:
        if isinstance(h, (bool, np.bool_)) or not isinstance(h, (int, np.integer)) or h < 1:
            raise ValueError(f"horizons must be integers >= 1, got {h!r}")
    if len(set(hs)) != len(hs):
        raise ValueError(f"duplicate horizons: {hs}")
    return [int(h) for h in hs]


def abnormal_returns(bars: pd.DataFrame, horizons: Sequence[int] = (1, 5, 20),
                     min_names: int = 5) -> pd.DataFrame:
    """Columns: date, ticker, ret, mkt_ret, then car_<k> for each k in horizons (all float64)."""
    hs = _check_horizons(horizons)
    df = validate_bars(bars)
    by_ticker = df.groupby("ticker", sort=False)["close"]
    ret = (df["close"] / by_ticker.shift(1) - 1).astype("float64")

    by_date = ret.groupby(df["date"])
    total = by_date.transform("sum")  # NaN skipped
    count = by_date.transform("count")
    own = ret.fillna(0.0)
    others = count - ret.notna().astype("int64")
    with np.errstate(divide="ignore", invalid="ignore"):
        mkt = (total - own) / others
    mkt = mkt.where(others >= max(min_names, 1)).astype("float64")
    ar = ret - mkt

    out = pd.DataFrame({"date": df["date"], "ticker": df["ticker"], "ret": ret, "mkt_ret": mkt})
    ar_by_ticker = ar.groupby(df["ticker"], sort=False)
    for k in hs:
        out[f"car_{k}"] = ar_by_ticker.transform(
            lambda s, k=k: s.rolling(k, min_periods=k).sum()).astype("float64")
    return out.reset_index(drop=True)
