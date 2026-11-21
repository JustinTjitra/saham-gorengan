import numpy as np
import pandas as pd
import pytest

from saham_gorengan.detectors.baselines import baseline_scores

D1 = "2024-01-02"
D2 = "2024-01-03"


def _frame(date=D1):
    return pd.DataFrame({
        "date": [date] * 4,
        "ticker": ["DDDD", "BBBB", "AAAA", "CCCC"],
        "ret_norm": [-0.50, 0.85, 0.90, 0.20],
        "vol_z": [np.nan, 4.0, 1.0, 5.0],
    })


def _by_ticker(out, col):
    return out.set_index("ticker")[col]


def test_rank_ret():
    r = _by_ticker(baseline_scores(_frame()), "rank_ret")
    assert r.to_dict() == {"AAAA": 1, "BBBB": 2, "CCCC": 3, "DDDD": 4}
    assert str(baseline_scores(_frame())["rank_ret"].dtype) == "Int64"


def test_rank_vol():
    r = _by_ticker(baseline_scores(_frame()), "rank_vol")
    assert r["CCCC"] == 1 and r["BBBB"] == 2 and r["AAAA"] == 3
    assert pd.isna(r["DDDD"])


def test_rule():
    out = baseline_scores(_frame())
    s = _by_ticker(out, "s_rule")
    assert s["AAAA"] == 0.0 and s["BBBB"] == 1.0 and s["CCCC"] == 0.0
    assert np.isnan(s["DDDD"])
    r = _by_ticker(out, "rank_rule")
    assert r["BBBB"] == 1 and r["AAAA"] == 2 and r["CCCC"] == 3
    assert pd.isna(r["DDDD"])
    assert out["s_rule"].dtype == "float64"
    assert out["date"].dtype == "datetime64[ns]"
    assert list(out["ticker"]) == sorted(out["ticker"])


def test_ties_broken_by_ticker():
    df = pd.DataFrame({"date": [D1] * 3, "ticker": ["CC", "AA", "BB"],
                       "ret_norm": [0.5] * 3, "vol_z": [1.0] * 3})
    r = _by_ticker(baseline_scores(df), "rank_ret")
    assert r.to_dict() == {"AA": 1, "BB": 2, "CC": 3}


def test_ranks_per_date():
    base = baseline_scores(_frame())
    two = pd.concat([_frame(), _frame(D2).assign(ret_norm=[0.1, 0.2, 0.3, 0.4])])
    out = baseline_scores(two)
    first = out[out["date"] == pd.Timestamp(D1)].reset_index(drop=True)
    pd.testing.assert_frame_equal(first, base)
    second = out[out["date"] == pd.Timestamp(D2)]
    assert _by_ticker(second, "rank_ret").to_dict() == {"CCCC": 1, "AAAA": 2, "BBBB": 3, "DDDD": 4}
    assert sorted(second["rank_ret"]) == [1, 2, 3, 4]


def test_bad_input():
    with pytest.raises(ValueError, match="vol_z"):
        baseline_scores(_frame().drop(columns="vol_z"))
    dup = pd.concat([_frame(), _frame().iloc[[0]]])
    with pytest.raises(ValueError):
        baseline_scores(dup)


def test_input_not_modified():
    df = _frame()
    before = df.copy(deep=True)
    baseline_scores(df)
    pd.testing.assert_frame_equal(df, before)
