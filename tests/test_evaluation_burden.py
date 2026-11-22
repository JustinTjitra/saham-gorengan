import math

import pandas as pd
import pytest

from saham_gorengan.evaluation.burden import alert_stats

DAYS = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"])
TICKERS = ["A", "B", "C", "D", "E"]
# (day index, ticker) -> rank for the flagged cells; 6 flags over A, B, C.
_FLAGS = {(0, "A"): 1, (0, "B"): 2, (1, "A"): 1, (1, "B"): 2, (2, "A"): 1, (3, "C"): 1}


def make_ranks() -> pd.DataFrame:
    rows = []
    for i, d in enumerate(DAYS):
        for j, t in enumerate(TICKERS):
            r = _FLAGS.get((i, t))
            if r is None:
                r = pd.NA if j == 4 else 3 + j  # unflagged: rank >= 3 or unranked
            rows.append((d, t, r))
    df = pd.DataFrame(rows, columns=["date", "ticker", "rank"])
    df["rank"] = df["rank"].astype("Int64")
    return df


def make_weak() -> pd.DataFrame:
    # 4 weak rows: 3 flagged ((0,A), (1,B), (3,C)) and 1 unflagged ((0,E)); plus non-weak and NA rows.
    rows = [
        (DAYS[0], "A", True), (DAYS[1], "B", True), (DAYS[3], "C", True), (DAYS[0], "E", True),
        (DAYS[2], "A", False), (DAYS[2], "D", pd.NA),
    ]
    df = pd.DataFrame(rows, columns=["date", "ticker", "weak"])
    df["weak"] = df["weak"].astype("boolean")
    return df


def test_counts():
    s = alert_stats(make_ranks(), k=2)
    assert s["flags_per_day"] == 1.5
    assert s["distinct_tickers"] == 3
    assert s["flags_per_ticker"] == 2.0
    assert all(type(v) is float for v in s.values())
    assert "share_flags_weak" not in s


def test_weak_overlap():
    s = alert_stats(make_ranks(), k=2, weak=make_weak())
    assert s["share_flags_weak"] == 0.5
    assert s["share_weak_flagged"] == 0.75


def test_no_flags():
    # make_ranks has rank 1; shift every rank up so none is 1
    r = make_ranks()
    r["rank"] = (r["rank"] + 1).astype("Int64")
    s = alert_stats(r, k=1, weak=make_weak())
    assert s["flags_per_day"] == 0
    assert s["distinct_tickers"] == 0
    assert math.isnan(s["flags_per_ticker"])
    assert math.isnan(s["share_flags_weak"])
    assert s["share_weak_flagged"] == 0.0


def test_bad_input():
    r, w = make_ranks(), make_weak()
    with pytest.raises(ValueError):
        alert_stats(r, k=0)
    with pytest.raises(ValueError):
        alert_stats(r, k=True)
    with pytest.raises(ValueError, match="rank"):
        alert_stats(r.drop(columns=["rank"]))
    with pytest.raises(ValueError, match="weak"):
        alert_stats(r, weak=w.drop(columns=["weak"]))
    with pytest.raises(ValueError):
        alert_stats(pd.concat([r, r.iloc[:1]]))
    with pytest.raises(ValueError):
        alert_stats(r, weak=pd.concat([w, w.iloc[:1]]))


def test_inputs_not_modified():
    r, w = make_ranks(), make_weak()
    r0, w0 = r.copy(deep=True), w.copy(deep=True)
    alert_stats(r, k=2, weak=w)
    pd.testing.assert_frame_equal(r, r0)
    pd.testing.assert_frame_equal(w, w0)
