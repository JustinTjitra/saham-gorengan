"""Robust z-score composite per liquidity bucket (PLAN.md 3.3)."""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from saham_gorengan.detectors.baselines import _rank

DEFAULT_COMPONENTS: tuple[str, ...] = ("ret_norm", "vol_z", "car_5", "runup_20")
_MAD_SCALE = 1.4826


def _check_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 1:
        raise ValueError(f"{name} must be an int >= 1")


def composite_scores(features: pd.DataFrame, components: Sequence[str] = DEFAULT_COMPONENTS,
                     min_group: int = 5, min_components: int = 2) -> pd.DataFrame:
    """Input: date, ticker, liq_bucket and the component columns (others ignored).
    Output: date, ticker, z_<component> for each component, score (float64), rank (Int64)."""
    components = list(components)
    if not components:
        raise ValueError("components must not be empty")
    _check_int("min_group", min_group)
    _check_int("min_components", min_components)
    for c in ("date", "ticker", "liq_bucket", *components):
        if c not in features.columns:
            raise ValueError(f"missing required column: {c}")

    df = pd.DataFrame({
        "date": pd.to_datetime(features["date"]).astype("datetime64[ns]"),
        "ticker": features["ticker"].astype("string"),
        "liq_bucket": features["liq_bucket"],
    })
    for c in components:
        df[c] = features[c].astype("float64")
    if df.duplicated(["date", "ticker"]).any():
        raise ValueError("duplicate (date, ticker) rows")
    df = df.sort_values(["date", "ticker"], kind="mergesort").reset_index(drop=True)

    ok = df[df["liq_bucket"].notna()]
    keys = [ok["date"], ok["liq_bucket"]]
    out = df[["date", "ticker"]].copy()
    zcols = []
    for c in components:
        g = ok.groupby(keys)[c]
        med = g.transform("median")
        mad = (ok[c] - med).abs().groupby(keys).transform("median")
        n = g.transform("count")
        denom = (_MAD_SCALE * mad).where(mad > 0)
        z = ((ok[c] - med) / denom).where(n >= min_group)
        out[f"z_{c}"] = z.reindex(df.index).astype("float64")
        zcols.append(f"z_{c}")

    z_all = out[zcols]
    out["score"] = z_all.mean(axis=1).where(z_all.notna().sum(axis=1) >= min_components).astype("float64")
    out["rank"] = _rank(out, "score")
    return out[["date", "ticker", *zcols, "score", "rank"]]
