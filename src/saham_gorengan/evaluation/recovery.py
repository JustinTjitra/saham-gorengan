"""Synthetic-injection recovery test (PLAN.md 3.4 sanity check)."""
from __future__ import annotations

from collections.abc import Sequence
from datetime import date

import numpy as np
import pandas as pd

from ..detectors.baselines import baseline_scores
from ..detectors.composite import composite_scores
from ..detectors.trend import trend_scores
from ..features.assemble import build_features
from ..testing import Pump, synthetic_bars
from .metrics import recall_at_k, window_metrics
from .placebo import random_ranks

_WARMUP = 80
_SPAN = 15  # default Pump: 10 pump days + 5 dump days


def run_recovery(seed: int = 0, n_tickers: int = 60, n_pumps: int = 6, k: int = 10, lead: int = 0,
                 start: date = date(2024, 1, 2), end: date = date(2024, 12, 31), daily_return: float = 0.15,
                 volume_mult: float = 8.0, include_random: bool = False,
                 include_trend: bool = False) -> dict[str, float]:
    """Returns recall@k per detector: {"rank_ret", "rank_vol", "rank_rule", "composite"}.

    Injects ``n_pumps`` default-parameter pump-and-dump episodes into a synthetic panel, runs
    the feature pipeline and the detectors, and scores recall@k against the injected windows
    (first pump day to last dump day, 15 trading days). ``daily_return`` and ``volume_mult``
    set the pump strength (dump return is -0.8 * daily_return). With ``include_random`` the
    result also has "random": a per-date permutation of the composite ranks, same scoring.
    With ``include_trend`` the result also has "rank_trend" (price-only trend_scores, defaults).

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
        pumps.append(Pump(ticker=tk, start=s.date(), daily_return=daily_return,
                          volume_mult=volume_mult, dump_return=-0.8 * daily_return))
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
    if include_trend:
        ranks["rank_trend"] = trend_scores(features[["date", "ticker", "ret"]])[["date", "ticker", "rank"]]
    if include_random:
        ranks["random"] = random_ranks(ranks["composite"], seed=seed)
    return {name: float(recall_at_k(window_metrics(r, windows, k=k, lead=lead)))
            for name, r in ranks.items()}


def recovery_sweep(daily_returns: Sequence[float] = (0.005, 0.01, 0.02, 0.15),
                   volume_mults: Sequence[float] = (1.0, 8.0), seeds: Sequence[int] = (0, 1),
                   n_tickers: int = 150, n_pumps: int = 10, k: int = 5) -> pd.DataFrame:
    """Recall@k per (daily_return, volume_mult, detector), averaged over ``seeds``."""
    rows = []
    for dr in daily_returns:
        for vm in volume_mults:
            runs = [run_recovery(seed=s, n_tickers=n_tickers, n_pumps=n_pumps, k=k,
                                 daily_return=dr, volume_mult=vm, include_random=True)
                    for s in seeds]
            for det in runs[0]:
                rows.append({"daily_return": float(dr), "volume_mult": float(vm), "detector": det,
                             "recall": float(np.mean([r[det] for r in runs]))})
    df = pd.DataFrame(rows, columns=["daily_return", "volume_mult", "detector", "recall"])
    return df.sort_values(["daily_return", "volume_mult", "detector"]).reset_index(drop=True)
