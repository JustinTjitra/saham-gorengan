"""Wire label windows, a feature panel and detector ranks into report inputs (PLAN.md 3.4)."""
from __future__ import annotations

from collections.abc import Iterable, Mapping

import pandas as pd

from .._load import Window
from ..detectors.baselines import baseline_scores
from ..detectors.composite import composite_scores
from ..detectors.iforest import iforest_scores
from .burden import alert_stats
from .metrics import window_metrics
from .placebo import placebo_windows, random_ranks
from .report import DetectorResult


def windows_frame(windows: Iterable[Window]) -> pd.DataFrame:
    """Columns window_id, ticker (string), start, end (datetime64[ns]), in input order."""
    ws = list(windows)
    return pd.DataFrame({
        "window_id": pd.Series([w.window_id for w in ws], dtype="string"),
        "ticker": pd.Series([w.ticker for w in ws], dtype="string"),
        "start": pd.to_datetime(pd.Series([w.start for w in ws], dtype="object")).astype("datetime64[ns]"),
        "end": pd.to_datetime(pd.Series([w.end for w in ws], dtype="object")).astype("datetime64[ns]"),
    })


def default_detectors(features: pd.DataFrame, include_iforest: bool = False) -> dict[str, pd.DataFrame]:
    """rank_ret, rank_vol, rank_rule, composite (and iforest if asked); columns date, ticker, rank."""
    base = baseline_scores(features[["date", "ticker", "ret_norm", "vol_z"]])
    out = {name: base[["date", "ticker", name]].rename(columns={name: "rank"})
           for name in ("rank_ret", "rank_vol", "rank_rule")}
    out["composite"] = composite_scores(features)[["date", "ticker", "rank"]]
    if include_iforest:
        out["iforest"] = iforest_scores(features)[["date", "ticker", "rank"]]
    return out


def evaluate(features: pd.DataFrame, windows: pd.DataFrame, detectors: Mapping[str, pd.DataFrame],
             k: int = 25, lead: int = 20, n_placebo: int = 20, seed: int = 0) -> list[DetectorResult]:
    """One DetectorResult per detector, in mapping order, ready for render_report."""
    if not detectors:
        raise ValueError("detectors must not be empty")
    if "liq_bucket" not in features.columns:
        raise ValueError("features is missing required column: liq_bucket")
    known = set(features["ticker"].astype(str))
    kept = windows[windows["ticker"].astype(str).isin(known)].reset_index(drop=True)
    if len(kept) == 0:
        raise ValueError("no windows with a ticker present in features")
    placebos = placebo_windows(kept, features[["date", "ticker", "liq_bucket"]],
                               n_per_window=n_placebo, seed=seed)
    results = []
    for name, ranks in detectors.items():
        results.append(DetectorResult(
            name=name,
            case_metrics=window_metrics(ranks, kept, k, lead),
            placebo_metrics=window_metrics(ranks, placebos, k, lead),
            random_metrics=window_metrics(random_ranks(ranks, seed=seed), kept, k, lead),
            burden=alert_stats(ranks, k),
        ))
    return results
