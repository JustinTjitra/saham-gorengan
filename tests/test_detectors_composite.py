"""Tests for the robust z-score composite detector (P4-02)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from saham_gorengan.detectors.composite import DEFAULT_COMPONENTS, composite_scores

D = "2024-01-02"


def _frame(rows):
    return pd.DataFrame(rows, columns=["date", "ticker", "liq_bucket", "a", "b"])


def _one(vals, bucket=1, start=0, date=D):
    return [(date, f"T{start + i:02d}", bucket, v, 1.0 * i) for i, v in enumerate(vals)]


def test_hand_z():
    df = _frame(_one([0, 0.1, 0.2, 0.3, 1.0]))
    out = composite_scores(df, components=["a"])
    assert list(out.columns) == ["date", "ticker", "z_a", "score", "rank"]
    exp = [-1.349, -0.6745, 0, 0.6745, 5.3959]
    assert out["z_a"].tolist() == pytest.approx(exp, abs=1e-3)
    assert out["z_a"].dtype == "float64" and out["score"].dtype == "float64"
    assert str(out["rank"].dtype) == "Int64"


def test_default_components():
    assert DEFAULT_COMPONENTS == ("ret_norm", "vol_z", "car_5", "runup_20")


def test_buckets_separate():
    b1 = [0, 0.1, 0.2, 0.3, 1.0]
    b2 = [0, 10, 20, 30, 100]
    out1 = composite_scores(_frame(_one(b1, 1) + _one(b2, 2, start=10)), components=["a"])
    out2 = composite_scores(_frame(_one([0, 0.1, 0.2, 0.3, 5.0], 1) + _one(b2, 2, start=10)),
                            components=["a"])
    z1 = out1[out1["ticker"] >= "T10"]["z_a"].tolist()
    z2 = out2[out2["ticker"] >= "T10"]["z_a"].tolist()
    assert z1 == z2
    assert z1 == pytest.approx([-1.349, -0.6745, 0, 0.6745, 5.3959], abs=1e-3)


def test_min_group():
    df = _frame(_one([0, 0.1, 0.2, 1.0]))
    assert composite_scores(df, components=["a"])["z_a"].isna().all()
    assert composite_scores(df, components=["a"], min_group=4)["z_a"].notna().all()


def test_score_and_rank():
    rows = _one([0, 0.1, 0.2, 0.3, 1.0])
    df = _frame(rows)
    df["b"] = [0.0, 0.1, 0.2, 0.3, 1.0]
    df.loc[4, "a"] = np.nan  # T04 loses a; group a has 4 values -> min_group 4
    out2 = composite_scores(df, components=["a", "b"], min_group=4)
    # a has 4 non-NaN (0,.1,.2,.3): T04 has only z_b
    assert pd.isna(out2.loc[4, "z_a"])
    assert pd.isna(out2.loc[4, "score"])  # min_components=2
    out1 = composite_scores(df, components=["a", "b"], min_group=4, min_components=1)
    assert out1.loc[4, "score"] == pytest.approx(out1.loc[4, "z_b"])
    assert out1.loc[4, "rank"] == 1
    assert pd.isna(out2.loc[4, "rank"])
    ranked = out1.sort_values("rank")["score"].tolist()
    assert ranked == sorted(ranked, reverse=True)


def test_na_bucket():
    rows = _one([0, 0.1, 0.2, 0.3, 1.0]) + [(D, "T99", None, 50.0, 50.0)]
    out = composite_scores(_frame(rows), components=["a", "b"], min_components=1)
    r = out[out["ticker"] == "T99"].iloc[0]
    assert pd.isna(r["z_a"]) and pd.isna(r["z_b"]) and pd.isna(r["score"]) and pd.isna(r["rank"])
    assert out[out["ticker"] != "T99"]["z_a"].notna().all()


def test_bad_input():
    df = _frame(_one([0, 0.1, 0.2, 0.3, 1.0]))
    with pytest.raises(ValueError, match="zzz"):
        composite_scores(df, components=["zzz"])
    with pytest.raises(ValueError, match="liq_bucket"):
        composite_scores(df.drop(columns="liq_bucket"), components=["a"])
    with pytest.raises(ValueError):
        composite_scores(pd.concat([df, df.iloc[[0]]]), components=["a"])
    with pytest.raises(ValueError):
        composite_scores(df, components=())
    with pytest.raises(ValueError):
        composite_scores(df, components=["a"], min_group=0)
    with pytest.raises(ValueError):
        composite_scores(df, components=["a"], min_components=True)


def test_input_not_modified():
    df = _frame(_one([0, 0.1, 0.2, 0.3, 1.0])).iloc[::-1]
    before = df.copy(deep=True)
    composite_scores(df, components=["a"])
    pd.testing.assert_frame_equal(df, before)


def test_per_date_and_sorted():
    df = _frame(_one([0, 0.1, 0.2, 0.3, 1.0], date="2024-01-03") + _one([0, 0.1, 0.2, 0.3, 1.0]))
    out = composite_scores(df, components=["a"])
    assert out["date"].is_monotonic_increasing
    assert out["z_a"].iloc[:5].tolist() == out["z_a"].iloc[5:].tolist()
    assert out.index.tolist() == list(range(10))
