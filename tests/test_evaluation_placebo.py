import numpy as np
import pandas as pd

from saham_gorengan.evaluation.metrics import window_metrics
from saham_gorengan.evaluation.placebo import placebo_windows, random_ranks

DAYS = pd.bdate_range("2024-01-01", periods=120)
TICKERS = [f"T{i:02d}" for i in range(40)]


def _panel():
    rows = []
    for i, t in enumerate(TICKERS):
        b = 1 if i < 20 else 2
        rows.append(pd.DataFrame({"date": DAYS, "ticker": t,
                                  "liq_bucket": pd.array([b] * len(DAYS), dtype="Int64")}))
    return pd.concat(rows, ignore_index=True)


def _windows():
    return pd.DataFrame({
        "window_id": ["w1", "w2", "w3"],
        "ticker": ["T00", "T25", "T01"],
        "start": [DAYS[10], DAYS[50], DAYS[30]],
        "end": [DAYS[19], DAYS[54], DAYS[30]],
    })


def _ndays(df):
    return [int(((DAYS >= s) & (DAYS <= e)).sum()) for s, e in zip(df["start"], df["end"])]


def test_lengths_match():
    w = _windows()
    p = placebo_windows(w, _panel(), n_per_window=10, seed=1)
    assert len(p) == 30
    real = dict(zip(w["window_id"], _ndays(w)))
    for oid, n in zip(p["orig_window_id"], _ndays(p)):
        assert n == real[oid]
    assert p["window_id"].iloc[0] == "w1-P00"
    assert list(p.index) == list(range(len(p)))


def test_same_bucket_and_other_ticker():
    p = placebo_windows(_windows(), _panel(), n_per_window=30, seed=2)
    b1 = p[p["orig_window_id"].isin(["w1", "w3"])]
    b2 = p[p["orig_window_id"] == "w2"]
    assert set(b1["ticker"]) <= set(TICKERS[:20])
    assert set(b2["ticker"]) <= set(TICKERS[20:])
    real = {"w1": "T00", "w2": "T25", "w3": "T01"}
    assert all(t != real[o] for t, o in zip(p["ticker"], p["orig_window_id"]))


def test_deterministic():
    a = placebo_windows(_windows(), _panel(), seed=5)
    b = placebo_windows(_windows(), _panel(), seed=5)
    c = placebo_windows(_windows(), _panel(), seed=6)
    pd.testing.assert_frame_equal(a, b)
    assert not a.equals(c)


def test_no_overlap_with_real_windows():
    # real windows on many tickers covering most of the calendar for them
    w = pd.DataFrame({
        "window_id": ["a", "b", "c"],
        "ticker": ["T00", "T01", "T02"],
        "start": [DAYS[0], DAYS[0], DAYS[40]],
        "end": [DAYS[59], DAYS[59], DAYS[80]],
    })
    p = placebo_windows(w, _panel(), n_per_window=50, seed=3)
    for t, s, e in zip(p["ticker"], p["start"], p["end"]):
        for rt, rs, re_ in zip(w["ticker"], w["start"], w["end"]):
            if t == rt:
                assert e < rs or s > re_


def test_random_ranks_permutes():
    rng = np.random.default_rng(0)
    rows = []
    for d in DAYS[:10]:
        r = np.arange(1, 21, dtype=float)
        r[rng.choice(20, 4, replace=False)] = np.nan
        rows.append(pd.DataFrame({"date": d, "ticker": TICKERS[:20],
                                  "rank": pd.array(r, dtype="Int64")}))
    ranks = pd.concat(rows, ignore_index=True)
    out = random_ranks(ranks, seed=1)
    assert out["rank"].dtype == "Int64"
    assert (out["date"].to_numpy() == ranks["date"].to_numpy()).all()
    assert (out["ticker"].to_numpy() == ranks["ticker"].to_numpy()).all()
    assert (out["rank"].isna().to_numpy() == ranks["rank"].isna().to_numpy()).all()
    for d, g in ranks.groupby("date"):
        o = out[out["date"] == d]
        assert sorted(g["rank"].dropna().tolist()) == sorted(o["rank"].dropna().tolist())
    assert not out["rank"].equals(ranks["rank"])
    pd.testing.assert_frame_equal(out, random_ranks(ranks, seed=1))


def test_random_ranker_hit_rate():
    n_t, n_d, L = 200, 250, 20
    days = pd.bdate_range("2023-01-02", periods=n_d)
    tick = [f"S{i:03d}" for i in range(n_t)]
    ranks = pd.DataFrame({
        "date": np.repeat(days.to_numpy(), n_t),
        "ticker": np.tile(tick, n_d),
        "rank": pd.array(np.tile(np.arange(1, n_t + 1), n_d), dtype="Int64"),
    })
    rr = random_ranks(ranks, seed=0)
    rng = np.random.default_rng(1)
    s = rng.integers(0, n_d - L + 1, size=500)
    t = rng.integers(0, n_t, size=500)
    wins = pd.DataFrame({
        "window_id": [f"p{i}" for i in range(500)],
        "ticker": [tick[i] for i in t],
        "start": days[s],
        "end": days[s + L - 1],
    })
    m = window_metrics(rr, wins, k=10, lead=0)
    hit = float(m["found"].astype(float).mean())
    print("hit rate", hit)
    assert 0.55 <= hit <= 0.73


def test_inputs_not_modified():
    panel, w = _panel(), _windows()
    p0, w0 = panel.copy(deep=True), w.copy(deep=True)
    placebo_windows(w, panel, seed=0)
    pd.testing.assert_frame_equal(panel, p0)
    pd.testing.assert_frame_equal(w, w0)
    ranks = pd.DataFrame({"date": DAYS[:5].repeat(2), "ticker": ["A", "B"] * 5,
                          "rank": pd.array([1, 2] * 5, dtype="Int64")})
    r0 = ranks.copy(deep=True)
    random_ranks(ranks, seed=0)
    pd.testing.assert_frame_equal(ranks, r0)


def test_delisted_ticker_not_used_after_last_row():
    days = pd.bdate_range("2024-01-02", periods=60)
    rows = []
    for t in ["AAAA", "BBBB", "CCCC"]:
        for d in days:
            rows.append((d, t, 1))
    # DDDD stops trading after day 10; it must never host a placebo starting later.
    rows += [(d, "DDDD", 1) for d in days[:10]]
    panel = pd.DataFrame(rows, columns=["date", "ticker", "liq_bucket"])
    win = pd.DataFrame({"window_id": ["w"], "ticker": ["AAAA"],
                        "start": [days[30]], "end": [days[34]]})
    out = placebo_windows(win, panel, n_per_window=50, seed=3)
    late = out[(out["ticker"] == "DDDD") & (out["start"] > days[9])]
    assert late.empty
