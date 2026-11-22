"""Tests for the PU ranker, leave-one-case-out (P4-04)."""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from saham_gorengan.detectors.composite import DEFAULT_COMPONENTS
from saham_gorengan.detectors.pu import pu_loco, pu_scores
from saham_gorengan.evaluation.metrics import window_metrics
from saham_gorengan.evaluation.splits import loco_splits
from saham_gorengan.features.assemble import build_features
from saham_gorengan.testing import Pump, synthetic_bars

STARTS = [30, 70, 110, 150, 190, 230]


@pytest.fixture(scope="module")
def panel():
    days = pd.bdate_range("2024-01-02", "2024-12-31")
    tickers = [f"SY{chr(65)}{chr(65 + i)}" for i in range(6)]
    pumps = [Pump(ticker=t, start=days[s].date()) for t, s in zip(tickers, STARTS)]
    bars = synthetic_bars(n_tickers=40, start=date(2024, 1, 2), end=date(2024, 12, 31),
                          seed=0, pumps=pumps)
    feats = build_features(bars)
    wins = pd.DataFrame({
        "window_id": [f"w{i}" for i in range(6)],
        "ticker": tickers,
        "start": [days[s] for s in STARTS],
        "end": [days[s + 14] for s in STARTS],
    })
    return feats, wins, days


def test_loco_finds_held_out(panel):
    feats, wins, _ = panel
    res = pu_loco(feats, wins, lead=0, embargo=20)
    assert set(res) == set(wins["window_id"])
    found = 0
    for _, w in wins.iterrows():
        m = window_metrics(res[w["window_id"]], wins[wins["window_id"] == w["window_id"]],
                           k=5, lead=0)
        found += int(m["found"].iloc[0])
    assert found >= 5


def test_never_trains_on_held_out(panel, monkeypatch):
    feats, wins, days = panel
    calls = []
    orig = LogisticRegression.fit

    def rec(self, X, y, *a, **k):
        calls.append((np.array(X), np.array(y)))
        return orig(self, X, y, *a, **k)

    monkeypatch.setattr(LogisticRegression, "fit", rec)
    splits = loco_splits(days, wins, lead=0, embargo=20)
    for sp in splits:
        calls.clear()
        pu_scores(feats, wins, sp)
        assert len(calls) == 1
        X, y = calls[0]
        comp = list(DEFAULT_COMPONENTS)
        f = feats.dropna(subset=comp)
        f = f[f["date"].isin(sp.train_days)]
        assert len(f) == len(X)
        w = wins[wins["window_id"] == sp.held_out].iloc[0]
        inside = ((f["ticker"] == w["ticker"]) & (f["date"] >= w["start"])
                  & (f["date"] <= w["end"]))
        assert not inside.any()
        assert not set(f["date"]) & set(sp.test_days)


def test_labels(panel, monkeypatch):
    feats, wins, days = panel
    calls = []
    orig = LogisticRegression.fit

    def rec(self, X, y, *a, **k):
        calls.append(np.array(y))
        return orig(self, X, y, *a, **k)

    monkeypatch.setattr(LogisticRegression, "fit", rec)
    sp = loco_splits(days, wins, lead=0, embargo=20)[2]
    pu_scores(feats, wins, sp)
    comp = list(DEFAULT_COMPONENTS)
    f = feats.dropna(subset=comp)
    f = f[f["date"].isin(sp.train_days)]
    n = 0
    for _, w in wins.iterrows():
        if w["window_id"] == sp.held_out:
            continue
        n += int(((f["ticker"] == w["ticker"]) & (f["date"] >= w["start"])
                  & (f["date"] <= w["end"])).sum())
    assert n > 0
    assert int(calls[0].sum()) == n


def test_no_positives_raises(panel):
    feats, wins, days = panel
    one = wins.iloc[[0]]
    (sp,) = loco_splits(days, one, lead=0, embargo=20)
    with pytest.raises(ValueError, match="w0"):
        pu_scores(feats, one, sp)


def test_output_shape(panel):
    feats, wins, days = panel
    sp = loco_splits(days, wins, lead=0, embargo=20)[0]
    out = pu_scores(feats, wins, sp)
    assert list(out.columns) == ["date", "ticker", "score", "rank"]
    assert out["score"].dtype == "float64" and str(out["rank"].dtype) == "Int64"
    assert set(out["date"]) <= set(sp.test_days)


def test_deterministic(panel):
    feats, wins, days = panel
    sp = loco_splits(days, wins, lead=0, embargo=20)[1]
    pd.testing.assert_frame_equal(pu_scores(feats, wins, sp), pu_scores(feats, wins, sp))


def test_inputs_not_modified(panel):
    feats, wins, days = panel
    f0, w0 = feats.copy(deep=True), wins.copy(deep=True)
    pu_loco(feats, wins, lead=0, embargo=20)
    pd.testing.assert_frame_equal(feats, f0)
    pd.testing.assert_frame_equal(wins, w0)


def test_training_matrix_standardised(panel, monkeypatch):
    # The spec standardises components with the training rows' mean and std before fitting.
    feats, wins, days = panel
    seen = []
    orig = LogisticRegression.fit

    def rec(self, X, y, *a, **k):
        seen.append(np.array(X))
        return orig(self, X, y, *a, **k)

    monkeypatch.setattr(LogisticRegression, "fit", rec)
    sp = loco_splits(days, wins, lead=0, embargo=20)[0]
    pu_scores(feats, wins, sp)
    X = seen[0]
    assert np.allclose(X.mean(axis=0), 0.0, atol=1e-9)
    sd = X.std(axis=0)
    assert np.all(np.isclose(sd, 1.0) | np.isclose(sd, 0.0))
