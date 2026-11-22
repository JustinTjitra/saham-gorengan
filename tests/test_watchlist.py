"""Tests for the watchlist writer (P6-02)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

import saham_gorengan.watchlist as wl
from saham_gorengan.detectors.composite import composite_scores
from saham_gorengan.features.assemble import build_features
from saham_gorengan.testing import Pump, synthetic_bars
from saham_gorengan.watchlist import DISCLAIMER, build_watchlist, explain, write_watchlist

DAYS = pd.bdate_range("2024-01-02", "2024-12-31")
PUMP_START = DAYS[150].date()
SCORE_DAY = DAYS[155].date()
PUMP_TICKER = "SYAC"


@pytest.fixture(scope="module")
def panel():
    bars = synthetic_bars(n_tickers=30, start=date(2024, 1, 2), end=date(2024, 12, 31), seed=0,
                          pumps=[Pump(ticker=PUMP_TICKER, start=PUMP_START)])
    feats = build_features(bars)
    return feats, composite_scores(feats)


def _row(**z):
    return pd.Series({f"z_{k}": v for k, v in z.items()})


def test_explain_format():
    comp = _row(vol_z=4.12, cumret_20=-2.34, ret_norm=1.86, amihud_20=np.nan)
    assert explain(pd.Series(dtype=float), comp, top_n=3) == "vol_z +4.1, cumret_20 -2.3, ret_norm +1.9"


def test_explain_no_components():
    comp = _row(vol_z=np.nan, ret_norm=np.nan)
    assert explain(pd.Series(dtype=float), comp) == "no components available"


def test_explain_tie_break_by_name():
    comp = _row(b=2.0, a=-2.0, c=2.0)
    assert explain(pd.Series(dtype=float), comp, top_n=2) == "a -2.0, b +2.0"


def test_build_watchlist(panel):
    feats, comp = panel
    out = build_watchlist(SCORE_DAY, feats, comp, k=10)
    assert list(out.columns) == ["date", "ticker", "rank", "score", "drivers"]
    assert str(out["rank"].dtype) == "Int64" and out["score"].dtype == "float64"
    assert str(out["drivers"].dtype) == "string"
    assert out["rank"].tolist() == sorted(out["rank"].tolist())
    assert (out["date"] == pd.Timestamp(SCORE_DAY)).all()
    assert PUMP_TICKER in out["ticker"].head(3).tolist()
    assert (out["drivers"].str.len() > 0).all()


def test_wording_guard(panel, monkeypatch):
    feats, comp = panel
    monkeypatch.setattr(wl, "explain", lambda *a, **k: "pump detected")
    with pytest.raises(ValueError):
        build_watchlist(SCORE_DAY, feats, comp)


def test_write_roundtrip(panel, tmp_path):
    feats, comp = panel
    df = build_watchlist(SCORE_DAY, feats, comp, k=5)
    path = write_watchlist(df, root=tmp_path)
    assert path == tmp_path / "watchlist" / f"{SCORE_DAY.year}" / f"{SCORE_DAY.isoformat()}.parquet"
    pd.testing.assert_frame_equal(pd.read_parquet(path), df)
    assert pq.read_schema(path).metadata[b"disclaimer"].decode() == DISCLAIMER
    assert not list(path.parent.glob("*.tmp-*"))


def test_refuses_repo_root(panel):
    feats, comp = panel
    df = build_watchlist(SCORE_DAY, feats, comp, k=5)
    docs = Path(wl.__file__).resolve().parents[2] / "docs"
    with pytest.raises(RuntimeError):
        write_watchlist(df, root=docs)


def test_missing_day(panel):
    feats, comp = panel
    with pytest.raises(ValueError, match="no scores for 2024-06-15"):
        build_watchlist(date(2024, 6, 15), feats, comp)


def test_bad_k(panel):
    feats, comp = panel
    with pytest.raises(ValueError):
        build_watchlist(SCORE_DAY, feats, comp, k=0)
