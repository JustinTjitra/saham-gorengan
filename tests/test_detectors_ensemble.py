"""Tests for the rank ensemble (P4-06)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from saham_gorengan.detectors.ensemble import ensemble_scores

D = "2024-01-02"


def _ranks(pairs, date=D):
    return pd.DataFrame({
        "date": [date] * len(pairs),
        "ticker": [t for t, _ in pairs],
        "rank": pd.array([r for _, r in pairs], dtype="Int64"),
    })


def _inputs():
    a = _ranks([("AAAA", 1), ("BBBB", 2), ("CCCC", 3), ("DDDD", 4)])
    b = _ranks([("AAAA", 2), ("BBBB", 1), ("CCCC", None), ("DDDD", None)])
    return {"A": a, "B": b}


def test_hand_example():
    out = ensemble_scores(_inputs(), min_detectors=2)
    assert list(out.columns) == ["date", "ticker", "n_detectors", "ens_score", "rank"]
    assert out["ticker"].tolist() == ["AAAA", "BBBB", "CCCC", "DDDD"]
    assert out["n_detectors"].tolist() == [2, 2, 1, 1]
    assert out["n_detectors"].dtype == "Int64"
    assert out["ens_score"].dtype == "float64"
    assert out["ens_score"].iloc[0] == pytest.approx(0.625)
    assert out["ens_score"].iloc[1] == pytest.approx(0.5)
    assert out["ens_score"].iloc[2:].isna().all()
    assert out["rank"].dtype == "Int64"
    assert out["rank"].tolist()[:2] == [2, 1]
    assert out["rank"].iloc[2:].isna().all()


def test_min_detectors_one():
    out = ensemble_scores(_inputs(), min_detectors=1)
    assert out["ens_score"].tolist() == pytest.approx([0.625, 0.5, 0.75, 1.0])
    assert out["rank"].tolist() == [2, 1, 3, 4]


def test_union_rows():
    a = _ranks([("AAAA", 1), ("BBBB", 2)])
    b = _ranks([("AAAA", 1), ("ZZZZ", 2)])
    out = ensemble_scores({"A": a, "B": b}, min_detectors=1)
    assert out["ticker"].tolist() == ["AAAA", "BBBB", "ZZZZ"]
    assert out["n_detectors"].tolist() == [2, 1, 1]


def test_bad_input():
    good = _inputs()
    with pytest.raises(ValueError):
        ensemble_scores({})
    with pytest.raises(ValueError, match="'A'"):
        ensemble_scores({"A": good["A"].drop(columns="rank"), "B": good["B"]})
    dup = pd.concat([good["A"], good["A"].iloc[:1]], ignore_index=True)
    with pytest.raises(ValueError, match="'A'"):
        ensemble_scores({"A": dup, "B": good["B"]})
    for bad in (0, True, 1.5):
        with pytest.raises(ValueError):
            ensemble_scores(good, min_detectors=bad)


def test_inputs_not_modified():
    inp = _inputs()
    before = {k: v.copy(deep=True) for k, v in inp.items()}
    ensemble_scores(inp)
    for k in inp:
        pd.testing.assert_frame_equal(inp[k], before[k])


def test_per_date_normalisation():
    # n_ranked is counted per date: 2 ranked on day 1, 4 on day 2.
    a = pd.concat([_ranks([("AAAA", 1), ("BBBB", 2)], date="2024-01-02"),
                   _ranks([("AAAA", 1), ("BBBB", 2), ("CCCC", 3), ("DDDD", 4)], date="2024-01-03")],
                  ignore_index=True)
    out = ensemble_scores({"A": a}, min_detectors=1)
    assert out["ens_score"].tolist() == pytest.approx([0.5, 1.0, 0.25, 0.5, 0.75, 1.0])
    assert out["rank"].tolist() == [1, 2, 1, 2, 3, 4]
