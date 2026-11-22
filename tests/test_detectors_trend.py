import numpy as np
import pandas as pd
import pytest

from saham_gorengan.detectors.trend import trend_scores
from saham_gorengan.evaluation.recovery import run_recovery
from saham_gorengan.features.assemble import build_features
from saham_gorengan.testing import assert_no_lookahead, synthetic_bars

HAND = 3.872983


def _one(rets, ticker="AAAA"):
    return pd.DataFrame({"date": pd.bdate_range("2024-01-02", periods=len(rets)),
                         "ticker": ticker, "ret": rets})


def test_hand_example():
    out = trend_scores(_one([0.01, 0.03, 0.02, 0.04]), window=4, min_periods=4)
    assert out["s_trend"].iloc[:3].isna().all()
    assert out["s_trend"].iloc[3] == pytest.approx(HAND, abs=1e-6)
    assert out["s_trend"].dtype == "float64"
    assert str(out["rank"].dtype) == "Int64"


def test_masked_rows_skipped():
    out = trend_scores(_one([0.01, 0.03, np.nan, 0.02, 0.04]), window=5, min_periods=4)
    assert out["s_trend"].iloc[-1] == pytest.approx(HAND, abs=1e-6)


def test_rank_order():
    d = pd.bdate_range("2024-01-02", periods=4)
    a = pd.DataFrame({"date": d, "ticker": "AAAA", "ret": [0.01, 0.03, 0.02, 0.04]})
    b = pd.DataFrame({"date": d, "ticker": "BBBB", "ret": [0.04, -0.03, 0.02, -0.01]})
    out = trend_scores(pd.concat([a, b]), window=4, min_periods=4)
    last = out[out["date"] == d[-1]].set_index("ticker")["rank"]
    assert last["AAAA"] == 1 and last["BBBB"] == 2


def test_no_lookahead():
    bars = synthetic_bars(n_tickers=6)
    assert_no_lookahead(lambda b: trend_scores(build_features(b)), bars)


def test_bad_args():
    df = _one([0.01, 0.03, 0.02, 0.04])
    with pytest.raises(ValueError):
        trend_scores(df, window=1, min_periods=1)
    with pytest.raises(ValueError):
        trend_scores(df, window=4, min_periods=1)
    with pytest.raises(ValueError):
        trend_scores(df, window=4, min_periods=5)
    with pytest.raises(ValueError):
        trend_scores(df, window=True, min_periods=2)
    with pytest.raises(ValueError):
        trend_scores(df, window=4, min_periods=True)
    with pytest.raises(ValueError):
        trend_scores(df.drop(columns="ret"))
    with pytest.raises(ValueError):
        trend_scores(pd.concat([df, df.iloc[[0]]]))


def test_recovery_trend_strong_price_only():
    vals = [run_recovery(seed=s, n_tickers=150, n_pumps=10, k=5, daily_return=0.02,
                         volume_mult=1.0, include_trend=True)["rank_trend"] for s in (0, 1)]
    assert np.mean(vals) >= 0.8


def test_recovery_default_unchanged():
    assert "rank_trend" not in run_recovery(seed=0)
