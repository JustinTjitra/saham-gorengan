"""Price-only trend-persistence detector: rolling t-statistic of the daily return drift."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .baselines import _rank


def _check_int(name: str, v: object, lo: int) -> None:
    if isinstance(v, bool) or not isinstance(v, (int, np.integer)) or v < lo:
        raise ValueError(f"{name} must be an int >= {lo}, got {v!r}")


def trend_scores(features: pd.DataFrame, window: int = 10, min_periods: int = 8) -> pd.DataFrame:
    """Input: date, ticker, ret (other columns ignored). Output: date, ticker, s_trend (float64), rank (Int64).

    s_trend = mean(ret) / std(ret, ddof=1) * sqrt(n) over the trailing ``window`` rows of each
    ticker (n = non-missing returns); NaN when n < min_periods or the std is 0 or NaN.
    """
    _check_int("window", window, 2)
    _check_int("min_periods", min_periods, 2)
    if min_periods > window:
        raise ValueError("min_periods must not exceed window")
    for c in ("date", "ticker", "ret"):
        if c not in features.columns:
            raise ValueError(f"missing required column: {c}")
    df = pd.DataFrame({
        "date": pd.to_datetime(features["date"]).astype("datetime64[ns]"),
        "ticker": features["ticker"].astype("string"),
        "ret": features["ret"].astype("float64"),
    })
    if df.duplicated(["date", "ticker"]).any():
        raise ValueError("duplicate (date, ticker) rows")
    df = df.sort_values(["date", "ticker"], kind="mergesort").reset_index(drop=True)

    roll = df.groupby("ticker", sort=False)["ret"].rolling(window, min_periods=1)
    mean = roll.mean().reset_index(level=0, drop=True)
    std = roll.std(ddof=1).reset_index(level=0, drop=True)
    n = roll.count().reset_index(level=0, drop=True)
    s = mean / std * np.sqrt(n)
    s = s.where((n >= min_periods) & (std > 0))
    df["s_trend"] = s.reindex(df.index).astype("float64")
    df["rank"] = _rank(df, "s_trend")
    return df[["date", "ticker", "s_trend", "rank"]]
