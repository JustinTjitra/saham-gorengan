from datetime import date

import pandas as pd
import pytest

from saham_gorengan.testing import assert_no_lookahead, synthetic_bars


@pytest.fixture(scope="module")
def bars():
    return synthetic_bars(n_tickers=5)


def _trail_mean(b):
    b = b.sort_values(["ticker", "date"])
    out = b[["date", "ticker"]].copy()
    out["ma20"] = b.groupby("ticker")["close"].transform(lambda s: s.rolling(20).mean())
    return out


def _leaky(b):
    b = b.sort_values(["ticker", "date"])
    out = b[["date", "ticker"]].copy()
    out["next_close"] = b.groupby("ticker")["close"].shift(-1)
    return out


def _fullmean(b):
    out = b[["date", "ticker"]].copy()
    out["dev"] = b["close"] - b.groupby("ticker")["close"].transform("mean")
    return out


def test_trailing_mean_passes(bars):
    assert_no_lookahead(_trail_mean, bars)


def test_leaky_shift_raises(bars):
    with pytest.raises(AssertionError) as e:
        assert_no_lookahead(_leaky, bars)
    msg = str(e.value)
    assert "next_close" in msg or "close" in msg
    assert "SY" in msg


def test_full_sample_mean_raises(bars):
    with pytest.raises(AssertionError, match="dev"):
        assert_no_lookahead(_fullmean, bars)


def test_input_unchanged(bars):
    before = bars.copy(deep=True)
    assert_no_lookahead(_trail_mean, bars)
    pd.testing.assert_frame_equal(bars, before)
    with pytest.raises(AssertionError):
        assert_no_lookahead(_leaky, bars)
    pd.testing.assert_frame_equal(bars, before)


def test_nullable_boolean_feature(bars):
    def f(b):
        b = b.sort_values(["ticker", "date"])
        out = b[["date", "ticker"]].copy()
        ma = b.groupby("ticker")["close"].transform(lambda s: s.rolling(20).mean())
        out["above"] = pd.array((b["close"] > ma).where(ma.notna(), pd.NA), dtype="boolean")
        return out

    assert_no_lookahead(f, bars)


def test_nullable_boolean_leak_detected(bars):
    def f(b):
        b = b.sort_values(["ticker", "date"])
        out = b[["date", "ticker"]].copy()
        nxt = b.groupby("ticker")["close"].shift(-1)
        out["up"] = pd.array((nxt > b["close"]).where(nxt.notna(), pd.NA), dtype="boolean")
        return out

    with pytest.raises(AssertionError, match="up"):
        assert_no_lookahead(f, bars)


def test_string_and_int64_columns(bars):
    def f(b):
        out = b[["date", "ticker"]].copy()
        out["label"] = pd.array(["x"] * len(b), dtype="string")
        out["n"] = b["frequency"]
        return out

    assert_no_lookahead(f, bars)


def test_alignment_by_key_not_position(bars):
    def f(b):
        out = _trail_mean(b)
        return out.sample(frac=1.0, random_state=len(b))  # shuffled order

    assert_no_lookahead(f, bars)


def test_missing_row_in_trunc_raises(bars):
    def f(b):
        out = _trail_mean(b)
        if b["date"].max() < bars["date"].max():
            out = out[out["ticker"] != "SYAA"]
        return out

    with pytest.raises(AssertionError, match="SYAA"):
        assert_no_lookahead(f, bars)


def test_missing_date_ticker_columns_raises(bars):
    with pytest.raises(ValueError):
        assert_no_lookahead(lambda b: _trail_mean(b).drop(columns="ticker"), bars)
    with pytest.raises(ValueError):
        assert_no_lookahead(lambda b: _trail_mean(b).drop(columns="date"), bars)


def test_n_checks_validation(bars):
    with pytest.raises(ValueError):
        assert_no_lookahead(_trail_mean, bars, n_checks=0)


def test_explicit_check_dates_catch_leak(bars):
    d = bars["date"].sort_values().unique()[100]
    with pytest.raises(AssertionError, match="2022"):
        assert_no_lookahead(_leaky, bars, check_dates=[pd.Timestamp(d).date()])


def test_check_dates_default_picks_last_date_and_skips_warmup(bars):
    seen = []

    def f(b):
        seen.append(b["date"].max())
        return _trail_mean(b)

    assert_no_lookahead(f, bars, n_checks=5)
    dates = sorted(bars["date"].unique())
    trunc_maxes = seen[1:]
    assert len(trunc_maxes) == 5
    assert trunc_maxes[-1] == dates[-1]
    assert min(trunc_maxes) >= dates[int(len(dates) * 0.2)]


def test_duplicate_output_rows_raise():
    bars = synthetic_bars(n_tickers=2)

    def dup(b):
        out = b[["date", "ticker", "close"]]
        return pd.concat([out, out], ignore_index=True)

    with pytest.raises(ValueError, match="duplicate"):
        assert_no_lookahead(dup, bars)
