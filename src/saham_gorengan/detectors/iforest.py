"""Isolation forest per liquidity bucket, walk-forward (PLAN.md 3.3)."""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from saham_gorengan.detectors.baselines import _rank
from saham_gorengan.detectors.composite import DEFAULT_COMPONENTS, _check_int


def iforest_scores(features: pd.DataFrame, components: Sequence[str] = DEFAULT_COMPONENTS,
                   train_days: int = 250, refit_every: int = 20, min_train: int = 200,
                   seed: int = 0) -> pd.DataFrame:
    """Input like composite_scores (date, ticker, liq_bucket, components). Output: date, ticker, score (float64), rank (Int64)."""
    components = list(components)
    if not components:
        raise ValueError("components must not be empty")
    if len(set(components)) != len(components):
        raise ValueError("components must be unique")
    for name, v in (("train_days", train_days), ("refit_every", refit_every),
                    ("min_train", min_train), ("seed", seed)):
        if name == "seed":
            if isinstance(v, bool) or not isinstance(v, (int, np.integer)):
                raise ValueError("seed must be an int")
        else:
            _check_int(name, v)
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

    day_idx = pd.Series(df["date"]).rank(method="dense").to_numpy().astype(int) - 1
    n_days = int(day_idx.max()) + 1 if len(df) else 0
    X = df[components].to_numpy()
    complete = ~np.isnan(X).any(axis=1) & df["liq_bucket"].notna().to_numpy()
    buckets = df["liq_bucket"].astype(object).to_numpy()
    score = np.full(len(df), np.nan)

    refits = list(range(train_days, n_days, refit_every))
    for k, r in enumerate(refits):
        nxt = refits[k + 1] if k + 1 < len(refits) else n_days
        train_mask = complete & (day_idx >= r - train_days) & (day_idx <= r - 1)
        score_mask = complete & (day_idx >= r) & (day_idx <= nxt - 1)
        if not score_mask.any():
            continue
        for b in pd.unique(buckets[score_mask]):
            in_b = buckets == b
            tr = train_mask & in_b
            if tr.sum() < min_train:
                continue
            model = IsolationForest(n_estimators=100, random_state=seed).fit(X[tr])
            sc = score_mask & in_b
            score[sc] = -model.score_samples(X[sc])

    out = df[["date", "ticker"]].copy()
    out["score"] = pd.Series(score, dtype="float64")
    out["rank"] = _rank(out, "score")
    return out
