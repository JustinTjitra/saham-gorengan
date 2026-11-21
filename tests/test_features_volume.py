from datetime import date

import numpy as np
import pandas as pd

from saham_gorengan.features.volume import volume_features
from saham_gorengan.testing import Pump, assert_no_lookahead, synthetic_bars


def _frame(volume, n=None, **extra):
    n = len(volume) if n is None else n
    df = pd.DataFrame({
        "date": pd.bdate_range("2024-01-02", periods=n),
        "ticker": "AAAA",
        "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0,
        "volume": np.asarray(volume, dtype="float64"),
        "value": np.asarray(volume, dtype="float64") * 100.0,
        "source": "test",
    })
    for k, v in extra.items():
        df[k] = v
    return df


def test_hand_example():
    logs = [10.0 if i % 2 == 0 else 11.0 for i in range(20)] + [13.0]
    out = volume_features(_frame(np.expm1(logs)))
    assert out["vol_z"].iloc[:20].isna().all()
    assert abs(out["vol_z"].iloc[20] - 2.5 / (1.4826 * 0.5)) < 1e-6
    assert abs(out["vol_z"].iloc[20] - 3.3725) < 1e-3


def test_constant_volume_is_nan():
    out = volume_features(_frame([1000.0] * 40))
    assert out["vol_z"].isna().all()


def test_pump_lights_up():
    bars = synthetic_bars(n_tickers=5, seed=0, pumps=[Pump("SYAB", date(2022, 6, 1))])
    out = volume_features(bars)
    days = pd.bdate_range(date(2022, 6, 1), periods=15)
    pump = out[(out["ticker"] == "SYAB") & out["date"].isin(days)]
    assert pump["vol_z"].mean() > 3
    others = out[(out["ticker"] != "SYAB") & out["vol_z"].notna()]
    assert -1 < others["vol_z"].median() < 1


def test_turnover_prefers_tradeable():
    vol = [1000.0, 2000.0, 3000.0]
    both = volume_features(_frame(vol, listed_shares=10000.0, tradeable_shares=4000.0))
    assert np.allclose(both["turnover"], np.array(vol) / 4000.0)
    listed = volume_features(_frame(vol, listed_shares=10000.0))
    assert np.allclose(listed["turnover"], np.array(vol) / 10000.0)
    none = volume_features(_frame(vol))
    assert none["turnover"].isna().all()
    assert none["turnover"].dtype == "float64"


def test_zero_vol_share():
    out = volume_features(_frame([1000.0] * 20 + [0.0] * 5), window=60, min_periods=20)
    assert out["zero_vol_share"].iloc[:19].isna().all()
    assert abs(out["zero_vol_share"].iloc[24] - 5 / 25) < 1e-12


def test_no_lookahead():
    assert_no_lookahead(volume_features, synthetic_bars(n_tickers=5))


def test_input_not_modified():
    bars = synthetic_bars(n_tickers=3)
    before = bars.copy(deep=True)
    out = volume_features(bars)
    pd.testing.assert_frame_equal(bars, before)
    assert list(out.columns) == ["date", "ticker", "vol_z", "turnover", "turnover_z",
                                 "value_z", "zero_vol_share"]
    assert all(out[c].dtype == "float64" for c in out.columns[2:])
    assert out["date"].dtype == "datetime64[ns]"
