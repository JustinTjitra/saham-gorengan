from datetime import date

import numpy as np
import pandas as pd
import pytest

from saham_gorengan.features.limits import limit_features
from saham_gorengan.testing import assert_no_lookahead, synthetic_bars


def _bars(ticker, days, closes):
    c = [float(x) for x in closes]
    return pd.DataFrame({
        "date": pd.to_datetime(days), "ticker": ticker,
        "open": c, "high": c, "low": c, "close": c,
        "volume": 1000.0, "source": "test",
    })


def _second(prev, close, day):
    d0 = pd.bdate_range(end=day, periods=2)[0]
    out = limit_features(_bars("AAAA", [d0, day], [prev, close]))
    return out.iloc[1]


@pytest.mark.parametrize("close,norm,ara,arb", [
    (135, 1.0, True, False),
    (120, 0.2 / 0.35, False, False),
    (65, -1.0, False, True),
])
def test_pct_regime_2024(close, norm, ara, arb):
    r = _second(100, close, "2024-01-02")
    assert r["ret_norm"] == pytest.approx(norm)
    assert r["ara_hit"] == ara and r["arb_hit"] == arb
    assert r["ret"] == pytest.approx(close / 100 - 1)


def test_asymmetric_2025():
    assert _second(100, 85, "2025-05-02")["ret_norm"] == pytest.approx(-1.0)
    assert bool(_second(100, 85, "2025-05-02")["arb_hit"])
    assert _second(100, 90, "2025-05-02")["ret_norm"] == pytest.approx(-0.10 / 0.15)


def test_ara_run():
    days = pd.bdate_range("2024-01-02", periods=5)
    out = limit_features(_bars("AAAA", days, [100, 135, 182, 244, 240]))
    assert out["ara_hit"].tolist() == [pd.NA, True, True, True, False]
    assert out["ara_run"].tolist() == [pd.NA, 1, 2, 3, 0]


def test_ara_run_per_ticker():
    # per-ticker grouping: runs of interleaved tickers must not mix
    days = pd.bdate_range("2024-01-02", periods=3)
    df = pd.concat([_bars("AAAA", days, [100, 135, 182]), _bars("BBBB", days, [100, 100, 135])])
    out = limit_features(df).set_index(["ticker", "date"])
    assert out.loc["AAAA", "ara_run"].tolist() == [pd.NA, 1, 2]
    assert out.loc["BBBB", "ara_run"].tolist() == [pd.NA, 0, 1]


def test_fixed_rp1_band():
    r = _second(8, 9, "2026-10-20")
    assert bool(r["ara_hit"])
    assert r["ret_norm"] == pytest.approx(1.0)


def test_first_row_na():
    out = limit_features(_bars("AAAA", ["2024-01-02", "2024-01-03"], [100, 110]))
    first = out.iloc[0]
    for c in ("ret", "ret_norm", "ara_hit", "arb_hit", "ara_run"):
        assert pd.isna(first[c])


def test_dtypes_and_order():
    bars = synthetic_bars(n_tickers=3)
    out = limit_features(bars)
    assert out.dtypes.astype(str).to_dict() == {
        "date": "datetime64[ns]", "ticker": "string", "ret": "float64", "ret_norm": "float64",
        "ara_hit": "boolean", "arb_hit": "boolean", "ara_run": "Int64"}
    assert len(out) == len(bars)
    assert isinstance(out.index, pd.RangeIndex)
    assert (out["date"].values == bars["date"].values).all()


def test_no_lookahead():
    assert_no_lookahead(limit_features, synthetic_bars(n_tickers=5))


def test_input_not_modified():
    bars = synthetic_bars(n_tickers=3)
    before = bars.copy(deep=True)
    limit_features(bars)
    pd.testing.assert_frame_equal(bars, before)


def test_rp1_stock_is_at_its_floor():
    # Since 2026-09-28 a stock can trade at Rp1; the fixed Rp1 ARB would put the
    # lower limit at 0, below the minimum price, so the stock is already at its ARB.
    row = _second(1, 1, pd.Timestamp("2026-10-20"))
    assert row["arb_hit"] == True  # noqa: E712
    assert row["ara_hit"] == False  # noqa: E712
    assert row["ret"] == 0.0
