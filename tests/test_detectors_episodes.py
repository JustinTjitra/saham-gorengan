import pandas as pd
import pytest

from saham_gorengan.detectors.episodes import build_episodes

DAYS = pd.bdate_range("2024-01-01", periods=20)
COLS = ["episode_id", "ticker", "start", "end", "n_flag_days", "best_rank"]


def _ranks(flags, ticker="AAAA", ranks=None):
    """flags: 1-based trading days that are flagged; others get rank 99."""
    ranks = ranks or {}
    return pd.DataFrame({
        "date": DAYS,
        "ticker": ticker,
        "rank": pd.array([ranks.get(i + 1, 5) if (i + 1) in flags else 99
                          for i in range(len(DAYS))], dtype="Int64"),
    })


FLAGS = [1, 2, 4, 9]


def _spans(out):
    return [(s, e, n) for s, e, n in zip(out["start"], out["end"], out["n_flag_days"])]


def _d(i):
    return DAYS[i - 1]


def test_merge_within_gap():
    out = build_episodes(_ranks(FLAGS), k=25, max_gap=2)
    assert _spans(out) == [(_d(1), _d(4), 3), (_d(9), _d(9), 1)]
    assert list(out.columns) == COLS
    assert str(out["episode_id"].dtype) == "string"
    assert str(out["ticker"].dtype) == "string"
    assert str(out["start"].dtype) == "datetime64[ns]"
    assert str(out["n_flag_days"].dtype) == "Int64"
    assert str(out["best_rank"].dtype) == "Int64"


def test_gap_zero():
    out = build_episodes(_ranks(FLAGS), max_gap=0)
    assert _spans(out) == [(_d(1), _d(2), 2), (_d(4), _d(4), 1), (_d(9), _d(9), 1)]


def test_best_rank_and_ids():
    out = build_episodes(_ranks(FLAGS, ranks={1: 7, 2: 3, 4: 9, 9: 12}), max_gap=2)
    assert out["best_rank"].tolist() == [3, 12]
    assert out["episode_id"].tolist() == ["AAAA-20240101", "AAAA-20240111"]


def test_min_flags():
    out = build_episodes(_ranks(FLAGS), max_gap=2, min_flags=2)
    assert _spans(out) == [(_d(1), _d(4), 3)]


def test_two_tickers():
    df = pd.concat([_ranks([1, 2]), _ranks([3, 4], ticker="BBBB")], ignore_index=True)
    out = build_episodes(df, max_gap=5)
    assert out["ticker"].tolist() == ["AAAA", "BBBB"]
    assert out["n_flag_days"].tolist() == [2, 2]
    assert out["start"].tolist() == [_d(1), _d(3)]


def test_gap_counts_trading_days_of_all_tickers():
    # BBBB has rows on days AAAA lacks; they still count as trading days.
    a = _ranks([1, 4]).iloc[[0, 3]]
    b = _ranks([], ticker="BBBB")
    out = build_episodes(pd.concat([a, b], ignore_index=True), max_gap=1)
    assert len(out) == 2


def test_empty():
    for df in (_ranks([]), pd.DataFrame({"date": [], "ticker": [], "rank": []})):
        out = build_episodes(df)
        assert out.empty
        assert list(out.columns) == COLS
        assert str(out["n_flag_days"].dtype) == "Int64"
        assert str(out["start"].dtype) == "datetime64[ns]"
        assert str(out["episode_id"].dtype) == "string"


def test_na_not_flagged():
    df = _ranks([1, 2])
    df.loc[0, "rank"] = pd.NA
    out = build_episodes(df)
    assert _spans(out) == [(_d(2), _d(2), 1)]


def test_bad_args():
    df = _ranks(FLAGS)
    with pytest.raises(ValueError):
        build_episodes(df, k=0)
    with pytest.raises(ValueError):
        build_episodes(df, max_gap=-1)
    with pytest.raises(ValueError):
        build_episodes(df, min_flags=0)
    with pytest.raises(ValueError):
        build_episodes(df, k=True)
    with pytest.raises(ValueError):
        build_episodes(pd.concat([df, df.iloc[[0]]], ignore_index=True))
    with pytest.raises(ValueError, match="rank"):
        build_episodes(df.drop(columns="rank"))


def test_input_not_modified():
    df = _ranks(FLAGS)
    before = df.copy()
    build_episodes(df)
    pd.testing.assert_frame_equal(df, before)
