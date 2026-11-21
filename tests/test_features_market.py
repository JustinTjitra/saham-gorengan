from datetime import date

import numpy as np
import pandas as pd
import pytest

from saham_gorengan.features.market import abnormal_returns
from saham_gorengan.testing import Pump, assert_no_lookahead, synthetic_bars


def _three():
    rows = []
    for tk, c2 in (("AAAA", 110.0), ("BBBB", 100.0), ("CCCC", 96.0)):
        for d, c in (("2024-01-02", 100.0), ("2024-01-03", c2)):
            rows.append({"date": pd.Timestamp(d), "ticker": tk, "open": c, "high": c, "low": c,
                         "close": c, "volume": 1000.0, "value": c * 1000.0, "source": "test"})
    return pd.DataFrame(rows)


def test_leave_one_out_hand_example():
    out = abnormal_returns(_three(), min_names=2)
    d2 = out[out["date"] == pd.Timestamp("2024-01-03")]
    assert np.allclose(d2["mkt_ret"], [-0.02, 0.03, 0.05])
    assert np.allclose(d2["car_1"], [0.12, -0.03, -0.09])
    assert list(out.columns) == ["date", "ticker", "ret", "mkt_ret", "car_1", "car_5", "car_20"]
    assert out["ret"].dtype == "float64" and out["car_20"].dtype == "float64"


def test_min_names():
    out = abnormal_returns(_three())
    assert out["mkt_ret"].isna().all()
    assert out["car_1"].isna().all()


def test_car_needs_full_window():
    out = abnormal_returns(synthetic_bars(n_tickers=8, seed=1), horizons=(1, 5))
    for _, g in out.groupby("ticker"):
        g = g.reset_index(drop=True)
        assert g["car_5"].iloc[:5].isna().all()
        assert abs(g["car_5"].iloc[5] - g["car_1"].iloc[1:6].sum()) < 1e-12
        assert (g["car_1"].dropna() == (g["ret"] - g["mkt_ret"]).dropna()).all()


def test_pump_shows_up():
    bars = synthetic_bars(n_tickers=10, seed=0, pumps=[Pump("SYAB", date(2022, 6, 1))])
    out = abnormal_returns(bars)
    days = pd.bdate_range("2022-06-01", periods=5)
    row = out[(out["ticker"] == "SYAB") & (out["date"] == days[-1])]
    assert row["car_5"].iloc[0] > 0.4


@pytest.mark.parametrize("h", [(0,), (5, -1), (5, 5), (True,), (1.5,)])
def test_bad_horizons_raise(h):
    with pytest.raises(ValueError):
        abnormal_returns(_three(), horizons=h, min_names=2)


def test_no_lookahead():
    assert_no_lookahead(abnormal_returns, synthetic_bars(n_tickers=8))


def test_input_not_modified():
    bars = _three()
    before = bars.copy(deep=True)
    abnormal_returns(bars, min_names=2)
    pd.testing.assert_frame_equal(bars, before)
