import numpy as np
import pandas as pd
import pytest

from saham_gorengan.features.liquidity import liquidity_features
from saham_gorengan.testing import assert_no_lookahead, synthetic_bars


def _frame(closes, ticker="AAAA", value=None, volume=1000.0):
    dates = pd.bdate_range("2024-01-01", periods=len(closes))
    c = np.asarray(closes, dtype="float64")
    return pd.DataFrame({"date": dates, "ticker": ticker, "open": c, "high": c, "low": c,
                         "close": c, "volume": volume,
                         "value": np.nan if value is None else value, "source": "test"})


def test_value_est_fallback():
    df = _frame([100.0, 200.0], value=[5e9, np.nan], volume=10.0)
    out = liquidity_features(df, window=2)
    assert out["value_est"].tolist() == [5e9, 2000.0]
    assert list(out.columns) == ["date", "ticker", "value_est", "med_value_20", "amihud_20", "liq_bucket"]
    assert str(out["date"].dtype) == "datetime64[ns]"
    assert str(out["ticker"].dtype) == "string"
    for c in ("value_est", "med_value_20", "amihud_20"):
        assert out[c].dtype == "float64"
    assert str(out["liq_bucket"].dtype) == "Int64"


def test_amihud_hand_example():
    out = liquidity_features(_frame([100.0, 110.0, 99.0], value=1e9), window=2)
    assert out["amihud_20"].iloc[2] == pytest.approx(0.1)
    assert np.isnan(out["amihud_20"].iloc[1])


def test_buckets_rank():
    frames = []
    for k in range(1, 11):
        f = _frame([100.0] * 25, ticker="ABCDEFGHIJ"[k - 1] * 4, value=1e9 * k)
        frames.append(f)
    out = liquidity_features(pd.concat(frames, ignore_index=True))
    last = out[out["date"] == out["date"].max()].sort_values("med_value_20")
    assert last["liq_bucket"].tolist() == [1, 1, 2, 2, 3, 3, 4, 4, 5, 5]


def test_too_few_names():
    frames = [_frame([100.0] * 25, ticker=t * 4, value=1e9 * (i + 1)) for i, t in enumerate("ABCD")]
    out = liquidity_features(pd.concat(frames, ignore_index=True), n_buckets=5)
    assert out["liq_bucket"].isna().all()
    assert out["med_value_20"].notna().any()


def test_bad_args():
    df = _frame([100.0] * 5, value=1e9)
    with pytest.raises(ValueError):
        liquidity_features(df, window=1)
    with pytest.raises(ValueError):
        liquidity_features(df, n_buckets=1)
    with pytest.raises(ValueError):
        liquidity_features(df, window=True)


def test_no_lookahead():
    assert_no_lookahead(liquidity_features, synthetic_bars(n_tickers=10))


def test_input_not_modified():
    bars = synthetic_bars(n_tickers=5)
    before = bars.copy(deep=True)
    liquidity_features(bars)
    pd.testing.assert_frame_equal(bars, before)
