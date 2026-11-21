"""Baseline rankers: limit-normalised return, abnormal volume, and a simple UMA-like rule (PLAN.md 3.3)."""
from __future__ import annotations

import numpy as np
import pandas as pd

_REQUIRED = ("date", "ticker", "ret_norm", "vol_z")


def _rank(df: pd.DataFrame, score: str, secondary: str | None = None) -> pd.Series:
    """Per-date rank, 1 = highest score, ties by ticker ascending; NA where score is NaN."""
    keys = ["date", score] + ([secondary] if secondary else []) + ["ticker"]
    asc = [True, False] + ([False] if secondary else []) + [True]
    ok = df[df[score].notna()].sort_values(keys, ascending=asc, kind="mergesort")
    ranks = ok.groupby("date").cumcount() + 1
    return ranks.reindex(df.index).astype("Int64")


def baseline_scores(features: pd.DataFrame, rule_ret_norm: float = 0.8,
                    rule_vol_z: float = 3.0) -> pd.DataFrame:
    """Input: columns date, ticker, ret_norm, vol_z (other columns ignored).
    Output columns: date, ticker, s_ret, s_vol, s_rule (float64), rank_ret, rank_vol, rank_rule (Int64)."""
    for c in _REQUIRED:
        if c not in features.columns:
            raise ValueError(f"missing required column: {c}")
    df = pd.DataFrame({
        "date": pd.to_datetime(features["date"]).astype("datetime64[ns]"),
        "ticker": features["ticker"].astype("string"),
        "s_ret": features["ret_norm"].astype("float64"),
        "s_vol": features["vol_z"].astype("float64"),
    })
    if df.duplicated(["date", "ticker"]).any():
        raise ValueError("duplicate (date, ticker) rows")
    df = df.sort_values(["date", "ticker"], kind="mergesort").reset_index(drop=True)

    passed = (df["s_ret"] >= rule_ret_norm) & (df["s_vol"] >= rule_vol_z)
    df["s_rule"] = pd.Series(np.where(passed, 1.0, 0.0), index=df.index).where(
        df["s_ret"].notna() & df["s_vol"].notna()).astype("float64")

    df["rank_ret"] = _rank(df, "s_ret")
    df["rank_vol"] = _rank(df, "s_vol")
    df["rank_rule"] = _rank(df, "s_rule", "s_ret")
    return df[["date", "ticker", "s_ret", "s_vol", "s_rule",
               "rank_ret", "rank_vol", "rank_rule"]]
