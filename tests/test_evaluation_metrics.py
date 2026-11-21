import numpy as np
import pandas as pd
import pytest

from saham_gorengan.evaluation.metrics import recall_at_k, window_metrics

DAYS = pd.bdate_range("2024-01-01", periods=30)


def _ranks(special=None, ticker="AAAA"):
    r = [30] * 30
    for d in special or {}:
        r[d - 1] = special[d]
    return pd.DataFrame({"date": DAYS, "ticker": ticker, "rank": pd.array(r, dtype="Int64")})


def _win(ticker="AAAA", wid="w1"):
    return pd.DataFrame({"window_id": [wid], "ticker": [ticker],
                         "start": [DAYS[10]], "end": [DAYS[19]]})


def test_found_inside_window():
    m = window_metrics(_ranks({15: 3, 16: 3}), _win(), k=25, lead=5)
    row = m.iloc[0]
    assert row["found"] is True or bool(row["found"]) is True
    assert row["n_days"] == 10
    assert row["share_in_topk"] == pytest.approx(0.2)
    assert row["first_flag_offset"] == 4


def test_found_in_lead():
    r = _ranks({8: 3})
    m = window_metrics(r, _win(), k=25, lead=5)
    assert bool(m["found"].iloc[0]) is True
    assert m["first_flag_offset"].iloc[0] == -3
    m2 = window_metrics(r, _win(), k=25, lead=2)
    assert bool(m2["found"].iloc[0]) is False
    assert pd.isna(m2["first_flag_offset"].iloc[0])


def test_not_found():
    m = window_metrics(_ranks(), _win())
    assert bool(m["found"].iloc[0]) is False
    assert m["share_in_topk"].iloc[0] == 0.0


def test_missing_ticker():
    m = window_metrics(_ranks(), _win("BBBB"))
    row = m.iloc[0]
    assert row["n_days"] == 0
    assert bool(row["found"]) is False
    assert np.isnan(row["share_in_topk"])
    assert pd.isna(row["first_flag_offset"])
    assert str(m["n_days"].dtype) == "Int64"
    assert str(m["found"].dtype) == "boolean"
    assert m["share_in_topk"].dtype == "float64"
    assert str(m["first_flag_offset"].dtype) == "Int64"


def test_recall():
    ranks = pd.concat([_ranks({15: 3}), _ranks(ticker="CCCC")], ignore_index=True)
    wins = pd.concat([_win("AAAA", "a"), _win("CCCC", "c"), _win("BBBB", "b")], ignore_index=True)
    m = window_metrics(ranks, wins, k=25, lead=5)
    assert list(m["window_id"]) == ["a", "c", "b"]
    assert recall_at_k(m) == 0.5
    assert np.isnan(recall_at_k(m.iloc[[2]]))


def test_bad_args():
    r, w = _ranks(), _win()
    with pytest.raises(ValueError):
        window_metrics(r, w, k=0)
    with pytest.raises(ValueError):
        window_metrics(r, w, lead=-1)
    with pytest.raises(ValueError):
        window_metrics(r, w, k=True)
    with pytest.raises(ValueError, match="rank"):
        window_metrics(r.drop(columns="rank"), w)


def test_inputs_not_modified():
    r, w = _ranks({15: 3}), _win()
    r0, w0 = r.copy(deep=True), w.copy(deep=True)
    window_metrics(r, w)
    pd.testing.assert_frame_equal(r, r0)
    pd.testing.assert_frame_equal(w, w0)


def test_duplicate_ranks_raise():
    r = _ranks()
    with pytest.raises(ValueError, match="duplicate"):
        window_metrics(pd.concat([r, r.iloc[:1]], ignore_index=True), _win())
