"""Synthetic-injection recovery test (PLAN.md 3.4 sanity check)."""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from ..detectors.baselines import baseline_scores
from ..detectors.composite import composite_scores
from ..features.assemble import build_features
from ..testing import Pump, synthetic_bars
from .metrics import recall_at_k, window_metrics

_WARMUP = 80
_SPAN = 15  # default Pump: 10 pump days + 5 dump days


def run_recovery(seed: int = 0, n_tickers: int = 60, n_pumps: int = 6, k: int = 10, lead: int = 0,
                 start: date = date(2024, 1, 2), end: date = date(2024, 12, 31)) -> dict[str, float]:
    """Returns recall@k per detector: {"rank_ret", "rank_vol", "rank_rule", "composite"}.

    Injects ``n_pumps`` default-parameter pump-and-dump episodes into a synthetic panel, runs
    the feature pipeline and the detectors, and scores recall@k against the injected windows
    (first pump day to last dump day, 15 trading days).

    The default dates are in 2024 on purpose: in 2022 the 7% ARB would make the synthetic dump
    days (-12%) look like corporate actions, and P2-08 would mask them.
    """
    days = pd.bdate_range(start, end)
    n_days = len(days)
    if n_days - _SPAN < _WARMUP:
        raise ValueError(f"range has {n_days} trading days; need at least {_WARMUP + _SPAN}")
    if n_pumps > n_tickers:
        raise ValueError(f"n_pumps ({n_pumps}) exceeds n_tickers ({n_tickers})")

    rng = np.random.default_rng(seed)
    all_tickers = [f"SY{chr(65 + i // 26)}{chr(65 + i % 26)}" for i in range(n_tickers)]
    chosen = rng.choice(n_tickers, size=n_pumps, replace=False)
    idx = rng.integers(_WARMUP, n_days - _SPAN + 1, size=n_pumps)

    pumps, rows = [], []
    for t, i in zip(chosen, idx):
        tk = all_tickers[int(t)]
        s, e = days[int(i)], days[int(i) + _SPAN - 1]
        pumps.append(Pump(ticker=tk, start=s.date()))
        rows.append({"window_id": f"PUMP-{tk}", "ticker": tk, "start": s, "end": e})
    windows = pd.DataFrame(rows)

    bars = synthetic_bars(n_tickers, start, end, seed, pumps)
    features = build_features(bars)
    base = baseline_scores(features[["date", "ticker", "ret_norm", "vol_z"]])
    comp = composite_scores(features)

    ranks = {
        "rank_ret": base[["date", "ticker", "rank_ret"]].rename(columns={"rank_ret": "rank"}),
        "rank_vol": base[["date", "ticker", "rank_vol"]].rename(columns={"rank_vol": "rank"}),
        "rank_rule": base[["date", "ticker", "rank_rule"]].rename(columns={"rank_rule": "rank"}),
        "composite": comp[["date", "ticker", "rank"]],
    }
    return {name: float(recall_at_k(window_metrics(r, windows, k=k, lead=lead)))
            for name, r in ranks.items()}
