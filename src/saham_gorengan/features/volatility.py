"""Range (Parkinson) volatility with limit-day censoring (PLAN.md 3.2, feature 6)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..bars import validate_bars
from .limits import limit_features


def _check_args(window, min_periods) -> tuple[int, int]:
    def is_int(v) -> bool:
        return isinstance(v, (int, np.integer)) and not isinstance(v, (bool, np.bool_))

    if not is_int(window) or window < 2:
        raise ValueError(f"window must be an integer >= 2, got {window!r}")
    if not is_int(min_periods) or not 1 <= min_periods <= window:
        raise ValueError(f"min_periods must be an integer in 1..window, got {min_periods!r}")
    return int(window), int(min_periods)


def volatility_features(bars: pd.DataFrame, window: int = 20, min_periods: int = 10,
                        board: str = "regular") -> pd.DataFrame:
    """Columns: date, ticker, parkinson, vol_20, censored_share_20 (all but the keys float64).

    ``parkinson = ln(high / low)^2 / (4 ln 2)`` per row. A row is censored when
    ``limit_features`` flags ``ara_hit`` or ``arb_hit`` (NA counts as not censored), because the
    limit cuts its range off. ``vol_20`` is ``sqrt(mean(parkinson))`` over the uncensored rows
    among the ticker's last ``window`` rows including D, NaN with fewer than ``min_periods`` of
    them. ``censored_share_20`` is the share of censored rows in that window, NaN until the
    ticker has ``window`` rows. The ``_20`` suffix is kept whatever ``window`` is.
    Same rows and order as ``validate_bars(bars)``. Uses only data up to and including day D.
    """
    window, min_periods = _check_args(window, min_periods)
    df = validate_bars(bars)
    lim = limit_features(bars, board)
    tk = df["ticker"]
    censored = (lim["ara_hit"].fillna(False).astype(bool).to_numpy()
                | lim["arb_hit"].fillna(False).astype(bool).to_numpy())
    cens = pd.Series(censored.astype("float64"), index=df.index)

    park = (np.log(df["high"] / df["low"]) ** 2 / (4 * np.log(2))).astype("float64")
    p_unc = park.where(~censored)

    def roll_mean(s: pd.Series, mp: int) -> pd.Series:
        return s.groupby(tk, sort=False).transform(
            lambda v: v.rolling(window, min_periods=mp).mean())

    vol = np.sqrt(roll_mean(p_unc, min_periods))
    share = roll_mean(cens, window)

    out = pd.DataFrame({
        "date": df["date"],
        "ticker": tk,
        "parkinson": park,
        "vol_20": vol.astype("float64"),
        "censored_share_20": share.astype("float64"),
    })
    return out.reset_index(drop=True)
