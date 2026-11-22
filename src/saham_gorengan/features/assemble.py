"""Assemble every per-day feature into one table, masking probable corporate-action days."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..bars import validate_bars
from ..corporate import corporate_action_suspects
from .limits import limit_features
from .liquidity import liquidity_features
from .market import abnormal_returns
from .runup import runup_features
from .tradesize import tradesize_features
from .volatility import volatility_features
from .volume import volume_features

_KEY = ["date", "ticker"]

FEATURE_COLUMNS: tuple[str, ...] = (
    "ret", "ret_norm", "ara_hit", "arb_hit", "ara_run",
    "mkt_ret", "car_1", "car_5", "car_20",
    "vol_z", "turnover", "turnover_z", "value_z", "zero_vol_share",
    "cumret_5", "cumret_20", "runup_20", "drawdown_20",
    "value_est", "med_value_20", "amihud_20", "liq_bucket",
    "parkinson", "vol_20", "censored_share_20",
    "value_per_trade", "vpt_z", "freq_z", "net_foreign",
)

# Features whose value uses earlier rows; masked on the rows following a corporate-action day.
WINDOW_FEATURES: tuple[str, ...] = (
    "ara_run", "car_5", "car_20", "vol_z", "turnover_z", "value_z", "zero_vol_share",
    "cumret_5", "cumret_20", "runup_20", "drawdown_20", "med_value_20", "amihud_20",
    "liq_bucket", "vol_20", "censored_share_20", "vpt_z", "freq_z",
)


def build_features(bars: pd.DataFrame, board: str = "regular", post_mask_rows: int = 60) -> pd.DataFrame:
    """Columns: date, ticker, masked ("boolean"), post_masked ("boolean"), then FEATURE_COLUMNS. Same rows and order as validate_bars(bars).

    Rows that ``corporate_action_suspects`` flags (probable splits, rights, bonus issues) get
    ``masked`` True and every feature missing (NaN / NA, dtype kept), not adjusted (PLAN.md 3.1).

    Caution: the masking uses P1-08 rule 2, which relies on Yahoo's after-the-fact adjusted
    close. That is acceptable for removing split days, which are announced in advance, but
    ``masked`` itself must never be used as a feature.

    ``post_masked`` is True on the ``post_mask_rows`` rows of the same ticker after a masked row
    (not on masked rows); there ``WINDOW_FEATURES`` are set missing because their windows span the
    price jump. ``post_mask_rows`` is an int >= 0 (bool rejected); 0 turns this off.
    """
    if isinstance(post_mask_rows, bool) or not isinstance(post_mask_rows, (int, np.integer)) \
            or post_mask_rows < 0:
        raise ValueError("post_mask_rows must be an int >= 0")
    df = validate_bars(bars)
    out = df[_KEY].copy()
    parts = [
        limit_features(df, board),
        abnormal_returns(df).drop(columns=["ret"]),
        volume_features(df),
        runup_features(df),
        liquidity_features(df),
        volatility_features(df, board=board),
        tradesize_features(df),
    ]
    for p in parts:
        out = out.merge(p, on=_KEY, how="left")
    sus = corporate_action_suspects(df, board)
    masked = sus["suspect"].fillna(False).astype(bool)
    out = out.merge(sus[_KEY].assign(masked=masked.astype("boolean")), on=_KEY, how="left")

    if len(out) != len(df) or out.duplicated(_KEY).any():
        raise AssertionError("feature join changed the row count or produced duplicate keys")
    out = out.set_index(pd.MultiIndex.from_frame(out[_KEY])).reindex(
        pd.MultiIndex.from_frame(df[_KEY])).reset_index(drop=True)

    mask = out["masked"].to_numpy(dtype=bool)
    for c in FEATURE_COLUMNS:
        out[c] = out[c].mask(mask)

    post = np.zeros(len(out), dtype=bool)
    if post_mask_rows > 0:
        for idx in out.groupby("ticker", sort=False).indices.values():
            idx = np.sort(idx)
            left = 0  # rows remaining in the post-mask window
            for i in idx:
                if mask[i]:
                    left = int(post_mask_rows)
                elif left > 0:
                    post[i] = True
                    left -= 1
    out["post_masked"] = pd.array(post, dtype="boolean")
    for c in WINDOW_FEATURES:
        out[c] = out[c].mask(post)
    return out[[*_KEY, "masked", "post_masked", *FEATURE_COLUMNS]]
