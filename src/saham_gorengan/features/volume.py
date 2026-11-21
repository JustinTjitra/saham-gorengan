"""Robust volume, turnover and value z-scores plus zero-volume share (PLAN.md 3.2, feature 3)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..bars import validate_bars

MAD_SCALE = 1.4826
TURNOVER_SCALE = 1e6


def _robust_z(x: np.ndarray, window: int, min_periods: int) -> np.ndarray:
    """Robust z of ``log1p(x)`` against the previous ``window`` values (current excluded)."""
    s = np.log1p(x)
    n = len(s)
    out = np.full(n, np.nan)
    if n == 0:
        return out
    # row i sees s[i-window:i]; left-pad with NaN so every row has a full-width window
    padded = np.concatenate([np.full(window, np.nan), s])
    win = np.lib.stride_tricks.sliding_window_view(padded, window)[:n]
    ok = ~np.isnan(win).all(axis=1)
    cnt = (~np.isnan(win)).sum(axis=1)
    rows = np.flatnonzero(ok & (cnt >= min_periods) & ~np.isnan(s))
    if len(rows) == 0:
        return out
    w = win[rows]
    med = np.nanmedian(w, axis=1)
    mad = np.nanmedian(np.abs(w - med[:, None]), axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (s[rows] - med) / (MAD_SCALE * mad)
    out[rows] = np.where(mad == 0, np.nan, z)
    return out


def _zero_share(volume: np.ndarray, window: int, min_periods: int) -> np.ndarray:
    """Share of zero volumes in the last ``window`` rows including the current one."""
    s = pd.Series(volume)
    zero = (s == 0).astype("float64").where(s.notna())
    return zero.rolling(window, min_periods=min_periods).mean().to_numpy()


def volume_features(bars: pd.DataFrame, window: int = 60, min_periods: int = 20) -> pd.DataFrame:
    """Columns: date, ticker, vol_z, turnover, turnover_z, value_z, zero_vol_share (all float64)."""
    df = validate_bars(bars)
    shares = df["tradeable_shares"].fillna(df["listed_shares"])
    turnover = (df["volume"] / shares.where(shares > 0)).astype("float64")

    n = len(df)
    vol_z = np.full(n, np.nan)
    turn_z = np.full(n, np.nan)
    val_z = np.full(n, np.nan)
    zshare = np.full(n, np.nan)
    volume = df["volume"].to_numpy(dtype="float64")
    value = df["value"].to_numpy(dtype="float64")
    turn = turnover.to_numpy(dtype="float64") * TURNOVER_SCALE
    for idx in df.groupby("ticker", sort=False).indices.values():
        vol_z[idx] = _robust_z(volume[idx], window, min_periods)
        turn_z[idx] = _robust_z(turn[idx], window, min_periods)
        val_z[idx] = _robust_z(value[idx], window, min_periods)
        zshare[idx] = _zero_share(volume[idx], window, min_periods)

    return pd.DataFrame({
        "date": df["date"],
        "ticker": df["ticker"],
        "vol_z": vol_z,
        "turnover": turnover,
        "turnover_z": turn_z,
        "value_z": val_z,
        "zero_vol_share": zshare,
    }).reset_index(drop=True)
