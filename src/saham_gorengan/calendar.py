"""Trading calendar and missing-day flags derived from the bar panel.

A missing day (no bar for a listed ticker on a trading day) is a suspension
proxy. It is reported as a flag and never forward-filled into a fake price.

Look-ahead note: the row for (D, ticker) depends only on bars dated D or
earlier, with one exception: the calendar itself is built from the whole panel
(median ticker count per date), so it uses information after D. Pass an
explicit ``calendar`` to avoid that.
"""
from __future__ import annotations

import math

import pandas as pd

from saham_gorengan.bars import validate_bars

_OUT_DTYPES = {"date": "datetime64[ns]", "ticker": "string", "missing": "bool", "gap_len": "Int64"}


def _empty_flags() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype=t) for c, t in _OUT_DTYPES.items()})


def trading_calendar(bars: pd.DataFrame, min_share: float = 0.5) -> pd.DatetimeIndex:
    """Sorted unique dates on which at least ceil(min_share * median daily ticker count) tickers have a bar."""
    if not (0 < min_share <= 1):
        raise ValueError(f"min_share must be in (0, 1], got {min_share}")
    df = validate_bars(bars)
    if df.empty:
        return pd.DatetimeIndex([], dtype="datetime64[ns]")
    counts = df.groupby("date")["ticker"].nunique()
    threshold = max(1, math.ceil(min_share * float(counts.median())))
    return pd.DatetimeIndex(counts.index[counts >= threshold].sort_values(), dtype="datetime64[ns]")


def missing_day_flags(bars: pd.DataFrame, calendar: pd.DatetimeIndex | None = None) -> pd.DataFrame:
    """One row per (date, ticker) for every calendar date from the ticker's first bar to the calendar's last date.

    Columns: date (datetime64[ns]), ticker (string), missing (bool), gap_len (Int64).
    """
    df = validate_bars(bars)
    if calendar is None:
        cal = trading_calendar(df)
    else:
        cal = pd.DatetimeIndex(calendar).unique().sort_values()
    cal = cal.astype("datetime64[ns]")
    df = df[df["date"].isin(cal)]
    if df.empty or len(cal) == 0:
        return _empty_flags()

    parts = []
    for ticker, dates in df.groupby(df["ticker"].astype(object))["date"]:
        days = cal[cal >= dates.min()]
        has = days.isin(dates)
        missing = ~has
        # run length of consecutive missing days: cumulative count reset at each present day
        grp = pd.Series(has).cumsum().to_numpy()
        gap = pd.Series(missing.astype(int)).groupby(grp).cumsum().to_numpy()
        parts.append(pd.DataFrame({"date": days, "ticker": ticker, "missing": missing, "gap_len": gap}))
    out = pd.concat(parts, ignore_index=True)
    out = out.astype(_OUT_DTYPES)
    return out.sort_values(["date", "ticker"], kind="stable").reset_index(drop=True)
