"""Leave-one-case-out splits with a trading-day embargo (PLAN.md 3.4)."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

_WIN_REQ = ("window_id", "ticker", "start", "end")


@dataclass(frozen=True)
class Split:
    held_out: str  # window_id
    train_days: pd.DatetimeIndex
    test_days: pd.DatetimeIndex


def _check_int(name: str, v: object, minimum: int) -> None:
    if isinstance(v, bool) or not isinstance(v, (int, np.integer)) or v < minimum:
        raise ValueError(f"{name} must be an int >= {minimum}, got {v!r}")


def loco_splits(days: Sequence, windows: pd.DataFrame, lead: int = 20,
                embargo: int = 60) -> list[Split]:
    """days: trading days (any order, duplicates allowed). windows: window_id, ticker, start, end.
    One Split per window, in windows order.

    Test days are the trading days from `lead` days before the window start through the window end.
    Train days are all trading days more than `embargo` positions away from every test day.
    A window containing no trading day is skipped."""
    _check_int("lead", lead, 0)
    _check_int("embargo", embargo, 0)
    for c in _WIN_REQ:
        if c not in windows.columns:
            raise ValueError(f"missing required column: {c}")
    wid = windows["window_id"].astype(str).to_numpy()
    if len(set(wid)) != len(wid):
        raise ValueError("windows has duplicate window_id values")

    t = pd.DatetimeIndex(pd.to_datetime(pd.Series(list(days)))).unique().sort_values()
    arr = t.to_numpy()
    starts = pd.to_datetime(windows["start"]).to_numpy()
    ends = pd.to_datetime(windows["end"]).to_numpy()
    pos = np.arange(len(t))

    out: list[Split] = []
    for w, s, e in zip(wid, starts, ends):
        i0 = int(np.searchsorted(arr, s, side="left"))
        i_end = int(np.searchsorted(arr, e, side="right"))  # exclusive
        if i_end <= i0:
            continue  # no trading day inside [start, end]
        first = max(0, i0 - lead)
        last = i_end - 1
        train_mask = (pos < first - embargo) | (pos > last + embargo)
        out.append(Split(held_out=str(w), train_days=t[train_mask], test_days=t[first:last + 1]))
    return out
