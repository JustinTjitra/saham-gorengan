import pandas as pd
import pytest

from saham_gorengan.bars import validate_bars
from saham_gorengan.weak_labels import ara_run_label

DAYS = pd.bdate_range("2024-03-04", periods=5)


def _bars(ticker, closes, days=DAYS):
    c = [float(x) for x in closes]
    return pd.DataFrame({
        "date": pd.to_datetime(days[: len(c)]), "ticker": ticker,
        "open": c, "high": c, "low": c, "close": c,
        "volume": 1000.0, "source": "test",
    })


def _aaaa():
    return _bars("AAAA", [100, 135, 182, 244, 240])


def test_three_day_run():
    out = ara_run_label(_aaaa(), min_run=3)
    assert list(out.columns) == ["date", "ticker", "ara_episode", "episode_id", "run_len"]
    assert out["ara_episode"].tolist() == [False, True, True, True, False]
    assert out["ara_episode"].dtype == "boolean"
    assert out["episode_id"].dtype == "string" and out["run_len"].dtype == "Int64"
    eid = f"AAAA-{DAYS[1]:%Y%m%d}"
    assert out["episode_id"].iloc[1:4].tolist() == [eid] * 3
    assert out["run_len"].iloc[1:4].tolist() == [3] * 3
    for i in (0, 4):
        assert pd.isna(out["episode_id"].iloc[i]) and pd.isna(out["run_len"].iloc[i])


def test_min_run_filters():
    out = ara_run_label(_aaaa(), min_run=4)
    assert not out["ara_episode"].any()
    assert out["episode_id"].isna().all() and out["run_len"].isna().all()


def test_two_tickers_independent():
    alone = ara_run_label(_aaaa(), min_run=3)
    b = _bars("BBBB", [100, 135, 130, 128, 126])
    both = ara_run_label(pd.concat([_aaaa(), b], ignore_index=True), min_run=3)
    assert not both.loc[both["ticker"] == "BBBB", "ara_episode"].any()
    a = both[both["ticker"] == "AAAA"].reset_index(drop=True)
    pd.testing.assert_frame_equal(a, alone)


@pytest.mark.parametrize("bad", [0, True, -1, 2.0, "3"])
def test_bad_min_run(bad):
    with pytest.raises(ValueError):
        ara_run_label(_aaaa(), min_run=bad)


def test_input_not_modified():
    bars = _aaaa()
    before = bars.copy(deep=True)
    ara_run_label(bars)
    pd.testing.assert_frame_equal(bars, before)


def test_same_rows_as_validate_bars():
    bars = pd.concat([_aaaa(), _bars("BBBB", [100, 101, 102, 103, 104])], ignore_index=True)
    v = validate_bars(bars)
    out = ara_run_label(bars)
    assert out["date"].tolist() == v["date"].tolist()
    assert out["ticker"].tolist() == v["ticker"].tolist()
    assert out.index.equals(pd.RangeIndex(len(v)))
