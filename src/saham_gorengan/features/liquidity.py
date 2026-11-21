"""Liquidity measures and daily liquidity buckets (PLAN.md 3.2, feature 5; 3.3)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..bars import validate_bars


def _check_int(name: str, v) -> int:
    if isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, np.integer)) or v < 2:
        raise ValueError(f"{name} must be an integer >= 2, got {v!r}")
    return int(v)


def liquidity_features(bars: pd.DataFrame, window: int = 20, n_buckets: int = 5) -> pd.DataFrame:
    """Columns: date, ticker, value_est, med_value_20, amihud_20 (float64), liq_bucket (Int64).

    ``value_est`` is ``value`` where present, else ``close * volume``. ``med_value_20`` is the
    rolling median of ``value_est`` and ``amihud_20`` the rolling mean of
    ``|ret| / value_est * 1e9`` (rows with no ``ret`` or a NaN or non-positive ``value_est`` are
    skipped), both over the ticker's last ``window`` rows including D; NaN until ``window``
    usable values exist. The ``_20`` suffix is kept whatever ``window`` is.
    ``liq_bucket`` ranks tickers per date by ``med_value_20`` (1 = least liquid,
    ``n_buckets`` = most liquid); NA where ``med_value_20`` is NaN, and NA for the whole date
    when fewer than ``n_buckets`` tickers have a value.
    Same rows and order as ``validate_bars(bars)``. Uses only data up to and including day D.
    """
    window = _check_int("window", window)
    n_buckets = _check_int("n_buckets", n_buckets)
    df = validate_bars(bars)
    tk = df["ticker"]
    close = df["close"]
    value_est = df["value"].where(df["value"].notna(), close * df["volume"]).astype("float64")
    ret = close / close.groupby(tk, sort=False).shift(1) - 1
    x = ret.abs() / value_est * 1e9
    x = x.where(ret.notna() & value_est.notna() & (value_est > 0))

    def roll(s: pd.Series, fn: str) -> pd.Series:
        return s.groupby(tk, sort=False).transform(
            lambda v: getattr(v.rolling(window, min_periods=window), fn)())

    med = roll(value_est, "median")
    amihud = roll(x, "mean")

    dates = df["date"]
    count = med.groupby(dates).transform("count")
    rank = med.groupby(dates).rank(method="first")
    bucket = np.ceil(rank / count * n_buckets)
    bucket = bucket.where(med.notna() & (count >= n_buckets))

    out = pd.DataFrame({
        "date": dates,
        "ticker": tk,
        "value_est": value_est,
        "med_value_20": med.astype("float64"),
        "amihud_20": amihud.astype("float64"),
        "liq_bucket": bucket.astype("Int64"),
    })
    return out.reset_index(drop=True)
