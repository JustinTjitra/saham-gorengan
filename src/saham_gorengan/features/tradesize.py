"""Trade-size and foreign-flow features, null-safe (PLAN.md 3.2, features 7-8)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..bars import validate_bars
from .volume import _robust_z


def tradesize_features(bars: pd.DataFrame, window: int = 60, min_periods: int = 20) -> pd.DataFrame:
    """Columns: date, ticker, value_per_trade, vpt_z, freq_z, net_foreign (all float64).

    ``value_per_trade = value_est / frequency`` (``value_est`` is ``value`` where present, else
    ``close * volume``); NaN where ``frequency`` is NA or 0. ``vpt_z`` and ``freq_z`` are per-ticker
    robust z-scores as in ``volume_features``. ``net_foreign = (foreign_buy - foreign_sell) / volume``,
    NaN when either foreign column or ``volume`` is NaN, or ``volume`` is 0.
    Same rows and order as ``validate_bars(bars)``. Uses only data up to and including day D.
    """
    df = validate_bars(bars)
    volume = df["volume"].astype("float64")
    value_est = df["value"].where(df["value"].notna(), df["close"] * df["volume"]).astype("float64")
    freq = df["frequency"].astype("float64")
    fb = df["foreign_buy"].astype("float64")
    fs = df["foreign_sell"].astype("float64")

    with np.errstate(divide="ignore", invalid="ignore"):
        vpt = (value_est / freq.where(freq != 0)).astype("float64")
        net = ((fb - fs) / volume.where(volume != 0)).astype("float64")

    n = len(df)
    vpt_z = np.full(n, np.nan)
    freq_z = np.full(n, np.nan)
    vpt_a = vpt.to_numpy(dtype="float64")
    freq_a = freq.to_numpy(dtype="float64")
    for idx in df.groupby("ticker", sort=False).indices.values():
        vpt_z[idx] = _robust_z(vpt_a[idx], window, min_periods)
        freq_z[idx] = _robust_z(freq_a[idx], window, min_periods)

    return pd.DataFrame({
        "date": df["date"],
        "ticker": df["ticker"],
        "value_per_trade": vpt,
        "vpt_z": vpt_z,
        "freq_z": freq_z,
        "net_foreign": net,
    }).reset_index(drop=True)
