import numpy as np
import pandas as pd
import pytest

from saham_gorengan.features.volatility import volatility_features
from saham_gorengan.testing import assert_no_lookahead, synthetic_bars

PARK = 0.1 ** 2 / (4 * np.log(2))


def _const(n=20, ticker="AAAA", price=100.0):
    dates = pd.bdate_range("2024-01-01", periods=n)
    c = np.full(n, price)
    return pd.DataFrame({"date": dates, "ticker": ticker, "open": c,
                         "high": c * np.exp(0.05), "low": c * np.exp(-0.05),
                         "close": c, "volume": 1000.0, "source": "test"})


def test_constant_range():
    out = volatility_features(_const())
    assert out["parkinson"].iloc[-1] == pytest.approx(0.0036067, abs=1e-7)
    assert out["vol_20"].iloc[-1] == pytest.approx(0.0600561, abs=1e-7)
    assert out["censored_share_20"].iloc[-1] == 0.0
    assert list(out.columns) == ["date", "ticker", "parkinson", "vol_20", "censored_share_20"]
    assert str(out["date"].dtype) == "datetime64[ns]"
    assert str(out["ticker"].dtype) == "string"
    for c in ("parkinson", "vol_20", "censored_share_20"):
        assert out[c].dtype == "float64"
    assert out.index.equals(pd.RangeIndex(20))


def test_limit_days_excluded():
    df = _const(price=10.0)
    close = df["close"].to_numpy().copy()
    open_ = df["open"].to_numpy().copy()
    high = df["high"].to_numpy().copy()
    low = df["low"].to_numpy().copy()
    for i in range(10, 20):
        open_[i] = close[i - 1]
        close[i] = close[i - 1] * 1.35
        high[i] = close[i] * 1.02
        low[i] = open_[i] * 0.98
    df["open"], df["close"], df["high"], df["low"] = open_, close, high, low
    out = volatility_features(df)
    assert out["censored_share_20"].iloc[-1] == 0.5
    assert out["vol_20"].iloc[-1] == pytest.approx(0.0600561, abs=1e-7)
    assert out["vol_20"].iloc[-1] == pytest.approx(np.sqrt(PARK), abs=1e-12)


def test_min_periods():
    out = volatility_features(_const(), min_periods=10)
    assert out["vol_20"].iloc[:9].isna().all()
    assert out["vol_20"].iloc[9:].notna().all()


def test_bad_args():
    df = _const()
    for kw in ({"window": 1}, {"min_periods": 0}, {"window": 20, "min_periods": 21},
               {"min_periods": True}):
        with pytest.raises(ValueError):
            volatility_features(df, **kw)


def test_no_lookahead():
    assert_no_lookahead(volatility_features, synthetic_bars(n_tickers=5))


def test_input_not_modified():
    df = _const()
    before = df.copy(deep=True)
    volatility_features(df)
    pd.testing.assert_frame_equal(df, before)
