import warnings

import numpy as np
import pandas as pd

from saham_gorengan.features.tradesize import tradesize_features
from saham_gorengan.testing import assert_no_lookahead, synthetic_bars


def _frame(n=1, ticker="AAAA", **cols):
    dates = pd.bdate_range("2024-01-01", periods=n)
    d = {"date": dates, "ticker": ticker, "open": 100.0, "high": 100.0, "low": 100.0,
         "close": 100.0, "volume": 1000.0, "source": "test"}
    d.update(cols)
    return pd.DataFrame(d)


def test_value_per_trade():
    df = _frame(3, value=1e6, frequency=pd.array([100, 0, pd.NA], dtype="Int64"))
    out = tradesize_features(df)
    assert out["value_per_trade"].iloc[0] == 1e4
    assert np.isnan(out["value_per_trade"].iloc[1])
    assert np.isnan(out["value_per_trade"].iloc[2])
    assert list(out.columns) == ["date", "ticker", "value_per_trade", "vpt_z", "freq_z", "net_foreign"]
    assert str(out["date"].dtype) == "datetime64[ns]"
    assert str(out["ticker"].dtype) == "string"
    for c in ("value_per_trade", "vpt_z", "freq_z", "net_foreign"):
        assert out[c].dtype == "float64"


def test_freq_z_hand_example():
    v = np.array([10.0, 11.0] * 10 + [13.0])
    freq = np.round(np.expm1(v)).astype("int64")
    out = tradesize_features(_frame(21, frequency=pd.array(freq, dtype="Int64")))
    assert abs(out["freq_z"].iloc[20] - 3.3725) < 1e-3


def test_net_foreign():
    df = _frame(2, foreign_buy=300.0, foreign_sell=100.0, volume=[1000.0, 0.0])
    out = tradesize_features(df)
    assert out["net_foreign"].iloc[0] == 0.2
    assert np.isnan(out["net_foreign"].iloc[1])


def test_yahoo_like_all_null():
    df = _frame(30)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        out = tradesize_features(df)
    assert len(out) == 30
    for c in ("value_per_trade", "vpt_z", "freq_z", "net_foreign"):
        assert out[c].isna().all()


def test_no_lookahead():
    assert_no_lookahead(tradesize_features, synthetic_bars(n_tickers=5))


def test_input_not_modified():
    df = _frame(3, frequency=pd.array([1, 2, 3], dtype="Int64"))
    before = df.copy(deep=True)
    tradesize_features(df)
    pd.testing.assert_frame_equal(df, before)
