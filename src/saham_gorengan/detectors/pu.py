"""Positive-unlabelled logistic ranker, leave-one-case-out (PLAN.md 3.3)."""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from saham_gorengan.detectors.baselines import _rank
from saham_gorengan.detectors.composite import DEFAULT_COMPONENTS
from saham_gorengan.evaluation.splits import Split, loco_splits


def _in_windows(df: pd.DataFrame, wins: pd.DataFrame) -> np.ndarray:
    """Boolean mask: row's ticker/date inside any window (inclusive), one vector pass per window."""
    mask = np.zeros(len(df), dtype=bool)
    tick = df["ticker"].to_numpy()
    date = df["date"].to_numpy()
    for t, s, e in zip(wins["ticker"].astype(str), pd.to_datetime(wins["start"]),
                       pd.to_datetime(wins["end"])):
        mask |= (tick == t) & (date >= np.datetime64(s)) & (date <= np.datetime64(e))
    return mask


def pu_scores(features: pd.DataFrame, windows: pd.DataFrame, split: Split,
              components: Sequence[str] = DEFAULT_COMPONENTS, C: float = 1.0) -> pd.DataFrame:
    """Output: date, ticker, score (float64), rank (Int64) for rows on split.test_days only."""
    components = list(components)
    if not components:
        raise ValueError("components must not be empty")
    for c in ("date", "ticker", *components):
        if c not in features.columns:
            raise ValueError(f"missing required column: {c}")
    for c in ("window_id", "ticker", "start", "end"):
        if c not in windows.columns:
            raise ValueError(f"missing required column: {c}")

    df = pd.DataFrame({
        "date": pd.to_datetime(features["date"]).astype("datetime64[ns]"),
        "ticker": features["ticker"].astype("string").astype(object),
    })
    for c in components:
        df[c] = features[c].astype("float64")
    if df.duplicated(["date", "ticker"]).any():
        raise ValueError("duplicate (date, ticker) rows")
    df = df.sort_values(["date", "ticker"], kind="mergesort").reset_index(drop=True)

    wid = windows["window_id"].astype(str)
    other = windows[(wid != split.held_out).to_numpy()]
    held = windows[(wid == split.held_out).to_numpy()]

    complete = df[components].notna().all(axis=1).to_numpy()
    train = df[df["date"].isin(split.train_days).to_numpy() & complete]
    test_mask = df["date"].isin(split.test_days).to_numpy()
    if len(held):
        assert not (_in_windows(train, held).any()), "held-out window rows in training set"
    assert not set(train["date"]) & set(split.test_days), "train and test days overlap"

    y = _in_windows(train, other).astype(int)
    if y.sum() == 0 or y.sum() == len(y):
        raise ValueError(f"window {split.held_out}: training rows have no "
                         f"{'positive' if y.sum() == 0 else 'negative'} examples")

    X = train[components].to_numpy()
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd = np.where(sd == 0, 1.0, sd)
    model = LogisticRegression(C=C, class_weight="balanced", max_iter=1000)
    model.fit((X - mu) / sd, y)

    out = df.loc[test_mask, ["date", "ticker"]].copy()
    Xt = df.loc[test_mask, components].to_numpy()
    ok = ~np.isnan(Xt).any(axis=1)
    score = np.full(len(out), np.nan)
    if ok.any():
        score[ok] = model.predict_proba((Xt[ok] - mu) / sd)[:, 1]
    out["score"] = score.astype("float64")
    out["ticker"] = out["ticker"].astype("string")
    out = out.reset_index(drop=True)
    out["rank"] = _rank(out, "score")
    return out[["date", "ticker", "score", "rank"]]


def pu_loco(features: pd.DataFrame, windows: pd.DataFrame, lead: int = 20, embargo: int = 60,
            components: Sequence[str] = DEFAULT_COMPONENTS, C: float = 1.0) -> dict[str, pd.DataFrame]:
    """window_id -> pu_scores output for that window's split (windows with no split are absent)."""
    days = pd.to_datetime(features["date"]).unique()
    splits = loco_splits(days, windows, lead=lead, embargo=embargo)
    return {s.held_out: pu_scores(features, windows, s, components, C) for s in splits}
