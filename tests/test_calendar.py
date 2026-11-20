import pandas as pd
import pytest

from saham_gorengan.bars import empty_bars, validate_bars
from saham_gorengan.calendar import missing_day_flags, trading_calendar


def make(rows):
    """rows: iterable of (date, ticker[, volume])."""
    recs = []
    for r in rows:
        d, t = r[0], r[1]
        vol = r[2] if len(r) > 2 else 1000.0
        recs.append({"date": d, "ticker": t, "open": 100.0, "high": 101.0, "low": 99.0,
                     "close": 100.0, "volume": vol, "source": "test"})
    return validate_bars(pd.DataFrame(recs))


DAYS = list(pd.date_range("2024-01-01", periods=6, freq="D"))
TICKERS = [f"TK{c}{c}" for c in "ABCDEFGHIJ"]


def test_calendar_drops_sparse_dates():
    rows = [(d, t) for d in DAYS[:5] for t in TICKERS] + [(DAYS[5], TICKERS[0])]
    cal = trading_calendar(make(rows))
    assert list(cal) == DAYS[:5]


def test_calendar_empty():
    cal = trading_calendar(empty_bars())
    assert isinstance(cal, pd.DatetimeIndex)
    assert len(cal) == 0


@pytest.mark.parametrize("share", [0, 1.5])
def test_calendar_bad_min_share(share):
    with pytest.raises(ValueError):
        trading_calendar(make([(DAYS[0], "AAAA")]), min_share=share)


def test_missing_flags_gap_len():
    rows = [(DAYS[i], "AAAA") for i in (0, 1, 4)] + [(d, "BBBB") for d in DAYS]
    out = missing_day_flags(make(rows), pd.DatetimeIndex(DAYS))
    a = out[out.ticker == "AAAA"]
    assert list(a.date) == DAYS
    assert list(a.missing) == [False, False, True, True, False, True]
    assert list(a.gap_len) == [0, 0, 1, 2, 0, 1]
    assert dict(out.dtypes.astype(str)) == {
        "date": "datetime64[ns]", "ticker": "string", "missing": "bool", "gap_len": "Int64"}


def test_rows_start_at_first_bar():
    rows = [(d, "BBBB") for d in DAYS] + [(d, "AAAA") for d in DAYS[2:]]
    out = missing_day_flags(make(rows), pd.DatetimeIndex(DAYS))
    assert out[out.ticker == "AAAA"].date.min() == DAYS[2]
    assert len(out[out.ticker == "AAAA"]) == 4


def test_zero_volume_is_not_missing():
    rows = [(DAYS[0], "AAAA", 0.0), (DAYS[1], "AAAA", float("nan")), (DAYS[2], "AAAA", 5.0)]
    out = missing_day_flags(make(rows), pd.DatetimeIndex(DAYS[:3]))
    assert not out.missing.any()
    assert list(out.gap_len) == [0, 0, 0]


def test_no_lookahead():
    rows = [(DAYS[i], "AAAA") for i in (0, 1, 4)] + [(d, "BBBB") for d in DAYS] \
        + [(d, "CCCC") for d in DAYS[2:4]]
    bars = make(rows)
    cal = pd.DatetimeIndex(DAYS)
    full = missing_day_flags(bars, cal)
    for d in cal:
        part = missing_day_flags(bars[bars.date <= d], cal[cal <= d])
        exp = full[full.date <= d]
        pd.testing.assert_frame_equal(part.reset_index(drop=True), exp.reset_index(drop=True))


def test_input_not_modified():
    bars = make([(DAYS[0], "AAAA"), (DAYS[2], "AAAA"), (DAYS[0], "BBBB")])
    before = bars.copy(deep=True)
    cal = pd.DatetimeIndex(DAYS[:3])
    trading_calendar(bars)
    missing_day_flags(bars, cal)
    pd.testing.assert_frame_equal(bars, before)
    assert list(cal) == DAYS[:3]


def test_empty_panel_flags():
    out = missing_day_flags(empty_bars())
    assert len(out) == 0
    assert dict(out.dtypes.astype(str)) == {
        "date": "datetime64[ns]", "ticker": "string", "missing": "bool", "gap_len": "Int64"}
