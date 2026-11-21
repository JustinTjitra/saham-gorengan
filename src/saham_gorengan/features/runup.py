"""Run-up and drawdown features (PLAN.md 3.2, feature 4)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..bars import validate_bars


def runup_features(bars: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Columns: date, ticker, cumret_5, cumret_20, runup_20, drawdown_20 (numeric ones float64).

    Windows count each ticker's own rows, not calendar days. ``cumret_5`` always uses k=5;
    ``cumret_20``, ``runup_20`` and ``drawdown_20`` use ``window`` rows, and keep their
    ``_20`` names whatever ``window`` is. ``runup_20`` is close over the window minimum
    (including day D) minus 1; ``drawdown_20`` is close over the window maximum minus 1 (<= 0).
    Same rows and order as ``validate_bars(bars)``. Uses only data up to and including day D.
    """
    if isinstance(window, (bool, np.bool_)) or not isinstance(window, (int, np.integer)) or window < 2:
        raise ValueError(f"window must be an integer >= 2, got {window!r}")
    window = int(window)
    df = validate_bars(bars)
    close = df["close"]
    g = close.groupby(df["ticker"], sort=False)

    def rolling(fn: str) -> pd.Series:
        return g.transform(lambda s: getattr(s.rolling(window, min_periods=window), fn)())

    out = pd.DataFrame({
        "date": df["date"],
        "ticker": df["ticker"],
        "cumret_5": close / g.shift(5) - 1,
        "cumret_20": close / g.shift(window) - 1,
        "runup_20": close / rolling("min") - 1,
        "drawdown_20": close / rolling("max") - 1,
    })
    for c in ("cumret_5", "cumret_20", "runup_20", "drawdown_20"):
        out[c] = out[c].astype("float64")
    return out.reset_index(drop=True)
