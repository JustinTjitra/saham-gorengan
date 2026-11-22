from datetime import date

import numpy as np
import pandas as pd
import pytest

from saham_gorengan.bars import validate_bars
from saham_gorengan.features.assemble import FEATURE_COLUMNS, WINDOW_FEATURES, build_features
from saham_gorengan.features.market import abnormal_returns
from saham_gorengan.features.runup import runup_features
from saham_gorengan.features.volume import volume_features
from saham_gorengan.testing import assert_no_lookahead, synthetic_bars


@pytest.fixture(scope="module")
def bars():
    return synthetic_bars(n_tickers=8)


@pytest.fixture(scope="module")
def feats(bars):
    return build_features(bars)


def test_columns_and_rows(bars, feats):
    ref = validate_bars(bars)
    assert list(feats.columns) == ["date", "ticker", "masked", "post_masked", *FEATURE_COLUMNS]
    assert len(feats) == len(ref)
    assert feats[["date", "ticker"]].reset_index(drop=True).equals(ref[["date", "ticker"]])
    assert not feats.duplicated(["date", "ticker"]).any()
    assert feats["masked"].dtype == "boolean"
    assert not feats["masked"].any()
    assert feats["post_masked"].dtype == "boolean"
    assert not feats["post_masked"].any()


def test_dtypes_preserved(feats):
    assert feats["ara_hit"].dtype == "boolean"
    assert feats["liq_bucket"].dtype == "Int64"
    assert feats["ara_run"].dtype == "Int64"
    assert feats["ret_norm"].dtype == np.float64


def _split_bars(n_after=0):
    n = 26 + n_after
    days = pd.bdate_range("2024-03-01", periods=n)
    close = [1000.0] * 25 + [200.0] * (1 + n_after)
    return pd.DataFrame({
        "date": days, "ticker": "SPLT", "open": close, "high": close, "low": close, "close": close,
        "volume": 1e6, "value": [c * 1e6 for c in close], "frequency": pd.array([1000] * n, dtype="Int64"),
        "source": "test",
    })


def test_split_day_masked():
    out = build_features(_split_bars())
    assert out["masked"].tolist() == [False] * 25 + [True]
    last = out.iloc[-1]
    assert last[list(FEATURE_COLUMNS)].isna().all()
    assert out.iloc[-2]["masked"] is False or not out.iloc[-2]["masked"]
    assert out.iloc[-2][["ret", "ret_norm"]].notna().all()
    # dtypes unchanged by masking
    assert out["ara_hit"].dtype == "boolean" and out["liq_bucket"].dtype == "Int64"
    assert out["ara_run"].dtype == "Int64" and out["ret_norm"].dtype == np.float64


def test_post_mask_window():
    out = build_features(_split_bars(n_after=70))
    assert len(out) == 96
    assert out["masked"].tolist() == [False] * 25 + [True] + [False] * 70
    pm = out["post_masked"]
    assert pm.dtype == "boolean"
    assert not pm.iloc[:26].any() and pm.iloc[26:86].all() and not pm.iloc[86:].any()
    wf = list(WINDOW_FEATURES)
    assert out.iloc[26:86][wf].isna().all(axis=None)
    assert pd.notna(out.iloc[26]["ret"])
    assert pd.notna(out.iloc[86]["cumret_5"])
    assert out["liq_bucket"].dtype == "Int64" and out["ara_run"].dtype == "Int64"
    assert out["ara_hit"].dtype == "boolean" and out["ret_norm"].dtype == np.float64


def test_post_mask_zero():
    bars = _split_bars(n_after=70)
    off = build_features(bars, post_mask_rows=0)
    on = build_features(bars)
    assert not off["post_masked"].any()
    assert off["post_masked"].dtype == "boolean"
    assert pd.notna(off.iloc[30]["cumret_5"])
    post = on["post_masked"].to_numpy(dtype=bool)
    expected = off.drop(columns="post_masked").copy()
    for c in WINDOW_FEATURES:
        expected[c] = expected[c].mask(post)
    pd.testing.assert_frame_equal(expected, on.drop(columns="post_masked"))


@pytest.mark.parametrize("bad", [-1, True])
def test_post_mask_bad_arg(bad):
    with pytest.raises(ValueError):
        build_features(_split_bars(), post_mask_rows=bad)


def test_window_features_subset():
    assert set(WINDOW_FEATURES) <= set(FEATURE_COLUMNS)
    assert list(WINDOW_FEATURES) == [c for c in FEATURE_COLUMNS if c in WINDOW_FEATURES]
    assert len(WINDOW_FEATURES) == 18


def test_matches_components(bars, feats):
    row = feats[(feats["ticker"] == "SYAC") & (feats["date"] == feats["date"].max())]
    assert len(row) == 1 and not row["masked"].iloc[0]
    key = ["date", "ticker"]
    for fn, col in ((volume_features, "vol_z"), (abnormal_returns, "car_5"), (runup_features, "runup_20")):
        ref = fn(bars).merge(row[key], on=key)
        assert ref[col].iloc[0] == pytest.approx(row[col].iloc[0], nan_ok=True)
    assert row[["vol_z", "car_5", "runup_20"]].notna().all(axis=None)


def test_no_lookahead():
    assert_no_lookahead(build_features, synthetic_bars(n_tickers=6))


def test_input_not_modified(bars):
    before = bars.copy(deep=True)
    build_features(bars)
    pd.testing.assert_frame_equal(bars, before)
