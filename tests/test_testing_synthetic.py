from datetime import date

import numpy as np
import pandas as pd
import pytest

from saham_gorengan.bars import validate_bars
from saham_gorengan.testing import Pump, synthetic_bars


def test_valid_and_deterministic():
    a = synthetic_bars(n_tickers=5, seed=3)
    b = synthetic_bars(n_tickers=5, seed=3)
    pd.testing.assert_frame_equal(a, b)
    pd.testing.assert_frame_equal(validate_bars(a), a)
    assert not a.equals(synthetic_bars(n_tickers=5, seed=4))
    assert list(a["ticker"].unique()) == ["SYAA", "SYAB", "SYAC", "SYAD", "SYAE"]
    assert (a["source"] == "synthetic").all()
    for bad in (0, 677):
        with pytest.raises(ValueError):
            synthetic_bars(n_tickers=bad)


def test_shape():
    s, e = date(2022, 1, 3), date(2022, 3, 31)
    df = synthetic_bars(n_tickers=7, start=s, end=e)
    assert len(df) == 7 * len(pd.bdate_range(s, e))


def test_pump_signature():
    p = Pump(ticker="SYAC", start=date(2022, 3, 7))
    df = synthetic_bars(n_tickers=5, seed=1, pumps=[p])
    t = df[df["ticker"] == "SYAC"].reset_index(drop=True)
    t["lr"] = np.log(t["close"] / t["close"].shift(1))
    i = int(t.index[t["date"] == pd.Timestamp(p.start)][0])
    pump = t.iloc[i:i + p.pump_days]
    dump = t.iloc[i + p.pump_days:i + p.pump_days + p.dump_days]
    assert pump["lr"].mean() > 0.08
    assert dump["lr"].mean() < -0.05
    window = t.index.isin(range(i, i + p.pump_days + p.dump_days))
    assert t.loc[window, "volume"].mean() > 4 * t.loc[~window, "volume"].mean()


def test_bad_pump_raises():
    for p in (
        Pump(ticker="SYZZ", start=date(2022, 3, 7)),  # unknown ticker
        Pump(ticker="SYAA", start=date(2022, 3, 5)),  # Saturday
        Pump(ticker="SYAA", start=date(2022, 12, 26)),  # runs past end
        Pump(ticker="SYAA", start=date(2023, 1, 2)),  # out of range
    ):
        with pytest.raises(ValueError):
            synthetic_bars(n_tickers=3, pumps=[p])
    a = Pump(ticker="SYAA", start=date(2022, 3, 7))
    b = Pump(ticker="SYAA", start=date(2022, 3, 14))
    with pytest.raises(ValueError):
        synthetic_bars(n_tickers=3, pumps=[a, b])
