from datetime import date

import numpy as np
import pandas as pd
import pytest

from saham_gorengan.features.runup import runup_features
from saham_gorengan.testing import Pump, assert_no_lookahead, synthetic_bars


def _bars(closes, ticker="AAAA"):
    dates = pd.bdate_range("2024-01-01", periods=len(closes))
    c = np.asarray(closes, dtype="float64")
    return pd.DataFrame({"date": dates, "ticker": ticker, "open": c, "high": c, "low": c,
                         "close": c, "volume": 1000.0, "value": c * 1000.0, "source": "test"})


LINEAR = [100.0 + i for i in range(21)]


def test_linear_climb():
    out = runup_features(_bars(LINEAR))
    last = out.iloc[-1]
    assert last["cumret_20"] == pytest.approx(0.2)
    assert last["cumret_5"] == pytest.approx(0.0434783, abs=1e-7)
    assert last["drawdown_20"] == 0.0
    assert last["runup_20"] == pytest.approx(0.1881188, abs=1e-7)
    assert list(out.columns) == ["date", "ticker", "cumret_5", "cumret_20", "runup_20", "drawdown_20"]
    assert str(out["date"].dtype) == "datetime64[ns]"
    assert str(out["ticker"].dtype) == "string"
    for c in ("cumret_5", "cumret_20", "runup_20", "drawdown_20"):
        assert out[c].dtype == "float64"


def test_drop_after_peak():
    out = runup_features(_bars(LINEAR + [108.0]))
    last = out.iloc[-1]
    assert last["drawdown_20"] == pytest.approx(-0.1)
    assert last["runup_20"] == pytest.approx(0.0588235, abs=1e-7)


def test_warmup_nan():
    out = runup_features(_bars(LINEAR))
    assert out["cumret_5"].iloc[:5].isna().all() and out["cumret_5"].iloc[5:].notna().all()
    assert out["runup_20"].iloc[:19].isna().all() and out["runup_20"].iloc[19:].notna().all()
    assert out["drawdown_20"].iloc[:19].isna().all()


def test_pump_then_dump():
    bars = synthetic_bars(n_tickers=5, seed=0, pumps=[Pump("SYAB", date(2022, 6, 1))])
    out = runup_features(bars)
    s = out[out["ticker"] == "SYAB"].set_index("date")
    days = pd.bdate_range(date(2022, 6, 1), periods=15)
    assert s.loc[days[9], "runup_20"] > 1.0
    assert s.loc[days[14], "drawdown_20"] < -0.3


@pytest.mark.parametrize("w", [1, 0, True, 2.5, "20"])
def test_bad_window(w):
    with pytest.raises(ValueError):
        runup_features(_bars(LINEAR), window=w)


def test_custom_window():
    out = runup_features(_bars(LINEAR), window=5)
    assert out["cumret_20"].iloc[5] == pytest.approx(105 / 100 - 1)
    assert out["runup_20"].iloc[:4].isna().all() and out["runup_20"].iloc[4] == pytest.approx(104 / 100 - 1)


def test_no_lookahead():
    assert_no_lookahead(runup_features, synthetic_bars(n_tickers=5))


def test_input_not_modified():
    bars = synthetic_bars(n_tickers=3).sample(frac=1.0, random_state=1)
    before = bars.copy()
    runup_features(bars)
    pd.testing.assert_frame_equal(bars, before)


def test_order_and_index_match_validate_bars():
    from saham_gorengan.bars import validate_bars
    bars = synthetic_bars(n_tickers=3).sample(frac=1.0, random_state=2)
    out = runup_features(bars)
    ref = validate_bars(bars)
    assert (out["date"] == ref["date"]).all() and (out["ticker"] == ref["ticker"]).all()
    assert out.index.equals(pd.RangeIndex(len(ref)))
