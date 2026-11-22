"""Rank ensemble: mean normalised rank across detectors (PLAN.md 3.3)."""
from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from saham_gorengan.detectors.baselines import _rank


def ensemble_scores(ranks: Mapping[str, pd.DataFrame], min_detectors: int = 2) -> pd.DataFrame:
    """ranks: detector name -> frame with date, ticker, rank (Int64; NA = unranked).
    Output: date, ticker, n_detectors (Int64), ens_score (float64), rank (Int64)."""
    if not ranks:
        raise ValueError("ranks must not be empty")
    if (isinstance(min_detectors, bool) or not isinstance(min_detectors, (int, np.integer))
            or min_detectors < 1):
        raise ValueError("min_detectors must be an int >= 1")

    parts = []
    for name, frame in ranks.items():
        for c in ("date", "ticker", "rank"):
            if c not in frame.columns:
                raise ValueError(f"detector {name!r}: missing required column: {c}")
        df = pd.DataFrame({
            "date": pd.to_datetime(frame["date"]).astype("datetime64[ns]"),
            "ticker": frame["ticker"].astype("string"),
            "rank": frame["rank"].astype("Int64"),
        })
        if df.duplicated(["date", "ticker"]).any():
            raise ValueError(f"detector {name!r}: duplicate (date, ticker) rows")
        n_ranked = df["rank"].groupby(df["date"]).transform("count")
        df["norm"] = (df["rank"].astype("float64") / n_ranked.astype("float64")).astype("float64")
        parts.append(df[["date", "ticker", "norm"]])

    long = pd.concat(parts, ignore_index=True)
    g = long.groupby(["date", "ticker"], sort=True)["norm"]
    out = pd.DataFrame({"n_detectors": g.count().astype("Int64"),
                        "mean": g.mean()}).reset_index()
    out["ens_score"] = out["mean"].where(out["n_detectors"] >= min_detectors).astype("float64")
    out["_neg"] = -out["ens_score"]
    out["rank"] = _rank(out, "_neg")
    out = out.sort_values(["date", "ticker"], kind="mergesort").reset_index(drop=True)
    return out[["date", "ticker", "n_detectors", "ens_score", "rank"]]
