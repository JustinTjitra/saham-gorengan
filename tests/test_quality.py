import numpy as np
import pandas as pd
import pytest

from saham_gorengan.quality import QUALITY_FLAGS, quality_flags, quality_summary


def _bar(date, ticker, close, volume=100.0, open_=None, high=None, low=None):
    o = close if open_ is None else open_
    h = max(o, close) if high is None else high
    lo = min(o, close) if low is None else low
    return {"date": date, "ticker": ticker, "open": o, "high": h, "low": lo,
            "close": close, "volume": volume, "source": "test"}


def _pair(day, prev_close, close, prev_day="2023-12-29", **kw):
    """Two bars for AAAA: the previous bar (close = prev_close) and the one under test."""
    return pd.DataFrame([_bar(prev_day, "AAAA", prev_close), _bar(day, "AAAA", close, **kw)])


def _last(df, col):
    return quality_flags(df)[col].iloc[-1]


def test_output_shape_and_dtypes():
    df = _pair("2024-01-02", 100.0, 101.0)
    out = quality_flags(df)
    assert list(out.columns) == ["date", "ticker", *QUALITY_FLAGS]
    assert all(str(out[c].dtype) == "boolean" for c in QUALITY_FLAGS)
    assert isinstance(out.index, pd.RangeIndex)


def test_zero_volume():
    df = pd.DataFrame([
        _bar("2024-01-02", "AAAA", 100.0, volume=0.0),
        _bar("2024-01-02", "BBBB", 100.0, volume=100.0),
        _bar("2024-01-02", "CCCC", 100.0, volume=np.nan),
    ])
    out = quality_flags(df)["zero_volume"]
    assert out.iloc[0] is True or out.iloc[0] == True  # noqa: E712
    assert out.iloc[1] == False  # noqa: E712
    assert out.iloc[2] is pd.NA


def test_stale_price():
    flat = _pair("2024-01-02", 100.0, 100.0)
    assert _last(flat, "stale_price") == True  # noqa: E712
    other = _pair("2024-01-02", 100.0, 102.0, open_=102.0, high=102.0, low=102.0)
    assert _last(other, "stale_price") == False  # noqa: E712
    # flat at the previous close but with a range is not stale
    ranged = _pair("2024-01-02", 100.0, 100.0, high=101.0)
    assert _last(ranged, "stale_price") == False  # noqa: E712
    assert quality_flags(flat)["stale_price"].iloc[0] is pd.NA


def test_beyond_limit_regular_2024():
    day = "2024-01-02"
    assert _last(_pair(day, 100.0, 135.0), "beyond_limit") == False  # noqa: E712
    assert _last(_pair(day, 100.0, 140.0), "beyond_limit") == True  # noqa: E712
    assert _last(_pair(day, 100.0, 64.0), "beyond_limit") == False  # noqa: E712
    assert _last(_pair(day, 100.0, 60.0), "beyond_limit") == True  # noqa: E712
    assert quality_flags(_pair(day, 100.0, 135.0))["beyond_limit"].iloc[0] is pd.NA


def test_beyond_limit_fixed_rp1():
    day, prev_day = "2026-10-20", "2026-10-19"
    assert _last(_pair(day, 8.0, 9.0, prev_day=prev_day), "beyond_limit") == False  # noqa: E712
    assert _last(_pair(day, 8.0, 11.0, prev_day=prev_day), "beyond_limit") == True  # noqa: E712


def test_beyond_limit_before_tables():
    df = _pair("2010-03-02", 100.0, 101.0, prev_day="2010-03-01")
    out = quality_flags(df)
    assert out["beyond_limit"].iloc[-1] is pd.NA
    assert out["off_tick"].iloc[-1] is pd.NA


def test_off_tick():
    day = "2024-01-02"
    cases = [(202.0, False), (203.0, True), (5010.0, True), (5025.0, False)]
    for close, expected in cases:
        assert _last(_pair(day, close, close), "off_tick") == expected, close


def test_unknown_board_raises_even_when_empty():
    df = _pair("2024-01-02", 100.0, 101.0)
    with pytest.raises(ValueError):
        quality_flags(df, board="nope")
    from saham_gorengan.bars import empty_bars
    with pytest.raises(ValueError):
        quality_flags(empty_bars(), board="nope")
    assert len(quality_flags(empty_bars())) == 0


def test_sorted_and_per_ticker_previous_close():
    df = pd.DataFrame([
        _bar("2024-01-03", "BBBB", 100.0),
        _bar("2024-01-02", "AAAA", 100.0),
        _bar("2024-01-03", "AAAA", 100.0),
        _bar("2024-01-02", "BBBB", 50.0),
    ])
    out = quality_flags(df)
    assert list(zip(out["date"].dt.strftime("%Y-%m-%d"), out["ticker"])) == [
        ("2024-01-02", "AAAA"), ("2024-01-02", "BBBB"),
        ("2024-01-03", "AAAA"), ("2024-01-03", "BBBB")]
    assert out["stale_price"].tolist() == [pd.NA, pd.NA, True, False]


def test_summary_counts():
    flags = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-02"] * 4),
        "ticker": ["AAAA", "BBBB", "AAAA", "CCCC"],
        "zero_volume": pd.array([True, True, False, pd.NA], dtype="boolean"),
        "stale_price": pd.array([False, False, False, False], dtype="boolean"),
        "beyond_limit": pd.array([pd.NA, pd.NA, pd.NA, pd.NA], dtype="boolean"),
        "off_tick": pd.array([True, pd.NA, True, False], dtype="boolean"),
    })
    s = quality_summary(flags)
    assert list(s.index) == list(QUALITY_FLAGS)
    assert list(s.columns) == ["n_true", "n_na", "share_true", "n_tickers"]
    assert s.loc["zero_volume"].tolist() == [2, 1, pytest.approx(2 / 3), 2]
    assert s.loc["stale_price"].tolist() == [0, 0, 0.0, 0]
    assert s.loc["beyond_limit", "n_true"] == 0
    assert s.loc["beyond_limit", "n_na"] == 4
    assert np.isnan(s.loc["beyond_limit", "share_true"])
    assert s.loc["off_tick"].tolist() == [2, 1, pytest.approx(2 / 3), 1]
    assert s["n_true"].dtype.kind == "i"


def test_input_not_modified():
    df = _pair("2024-01-02", 100.0, 101.0)
    before = df.copy(deep=True)
    quality_flags(df)
    pd.testing.assert_frame_equal(df, before)
