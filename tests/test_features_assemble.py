from datetime import date

import numpy as np
import pandas as pd
import pytest

from saham_gorengan.bars import validate_bars
from saham_gorengan.features.assemble import FEATURE_COLUMNS, build_features
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
    assert list(feats.columns) == ["date", "ticker", "masked", *FEATURE_COLUMNS]
    assert len(feats) == len(ref)
    assert feats[["date", "ticker"]].reset_index(drop=True).equals(ref[["date", "ticker"]])
    assert not feats.duplicated(["date", "ticker"]).any()
    assert feats["masked"].dtype == "boolean"
    assert not feats["masked"].any()


def test_dtypes_preserved(feats):
    assert feats["ara_hit"].dtype == "boolean"
    assert feats["liq_bucket"].dtype == "Int64"
    assert feats["ara_run"].dtype == "Int64"
    assert feats["ret_norm"].dtype == np.float64


def _split_bars():
    days = pd.bdate_range("2024-03-01", periods=26)
    close = [1000.0] * 25 + [200.0]
    return pd.DataFrame({
        "date": days, "ticker": "SPLT", "open": close, "high": close, "low": close, "close": close,
        "volume": 1e6, "value": [c * 1e6 for c in close], "frequency": pd.array([1000] * 26, dtype="Int64"),
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
