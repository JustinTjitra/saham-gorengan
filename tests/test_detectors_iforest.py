import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import IsolationForest

from saham_gorengan.detectors.composite import DEFAULT_COMPONENTS
from saham_gorengan.detectors.iforest import iforest_scores


def _panel(n_tickers=30, n_days=300, buckets=None, seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2020-01-01", periods=n_days)
    tickers = [f"T{i:02d}" for i in range(n_tickers)]
    idx = pd.MultiIndex.from_product([dates, tickers], names=["date", "ticker"])
    df = idx.to_frame(index=False)
    if buckets is None:
        df["liq_bucket"] = "A"
    else:
        df["liq_bucket"] = df["ticker"].map(buckets)
    for c in DEFAULT_COMPONENTS:
        df[c] = rng.standard_normal(len(df))
    return df, dates


def test_outlier_scores_highest():
    df, dates = _panel()
    mask = (df["date"] == dates[290]) & (df["ticker"] == "T00")
    for c in DEFAULT_COMPONENTS:
        df.loc[mask, c] = 8.0
    out = iforest_scores(df, train_days=250, refit_every=20, min_train=200)
    row = out[(out["date"] == dates[290]) & (out["ticker"] == "T00")]
    assert int(row["rank"].iloc[0]) == 1
    assert list(out.columns) == ["date", "ticker", "score", "rank"]
    assert out["score"].dtype == "float64" and str(out["rank"].dtype) == "Int64"


def test_training_strictly_before(monkeypatch):
    df, dates = _panel(n_tickers=10, n_days=120)
    # map each feature row back to its date via the exact values of the first component
    lookup = dict(zip(df[DEFAULT_COMPONENTS[0]].to_numpy(), df["date"]))
    records = []
    orig_fit = IsolationForest.fit

    def fit(self, X, y=None, sample_weight=None):
        train_dates = [lookup[v] for v in np.asarray(X)[:, 0]]
        records.append((max(train_dates), min(train_dates)))
        return orig_fit(self, X, y, sample_weight)

    monkeypatch.setattr(IsolationForest, "fit", fit)
    orig_score = IsolationForest.score_samples
    score_dates = []

    def score_samples(self, X):
        score_dates.append(min(lookup[v] for v in np.asarray(X)[:, 0]))
        return orig_score(self, X)

    monkeypatch.setattr(IsolationForest, "score_samples", score_samples)
    iforest_scores(df, train_days=50, refit_every=20, min_train=100)
    assert len(records) == len(score_dates) >= 3
    for (tmax, tmin), sdate in zip(records, score_dates):
        assert tmax < sdate  # training strictly before the first scored day of the block
    assert records[0][0] == dates[49] and records[0][1] == dates[0]
    assert score_dates[0] == dates[50]


def test_warmup_nan():
    df, dates = _panel(n_tickers=10, n_days=120)
    out = iforest_scores(df, train_days=50, refit_every=20, min_train=100)
    early = out[out["date"] < dates[50]]
    assert early["score"].isna().all() and early["rank"].isna().all()
    late = out[out["date"] >= dates[50]]
    assert late["score"].notna().all()


def test_min_train_skips_bucket():
    buckets = {f"T{i:02d}": ("big" if i < 8 else "small") for i in range(10)}
    df, dates = _panel(n_tickers=10, n_days=120, buckets=buckets)
    # small bucket: 2 tickers * 50 days = 100 rows < 150; big: 8*50 = 400
    out = iforest_scores(df, train_days=50, refit_every=20, min_train=150)
    out = out.merge(df[["date", "ticker", "liq_bucket"]], on=["date", "ticker"])
    late = out[out["date"] >= dates[50]]
    assert late[late["liq_bucket"] == "small"]["score"].isna().all()
    assert late[late["liq_bucket"] == "big"]["score"].notna().all()


def test_deterministic_and_input_untouched():
    df, _ = _panel(n_tickers=10, n_days=120)
    before = df.copy()
    a = iforest_scores(df, train_days=50, refit_every=20, min_train=100, seed=3)
    b = iforest_scores(df, train_days=50, refit_every=20, min_train=100, seed=3)
    pd.testing.assert_frame_equal(a, b)
    pd.testing.assert_frame_equal(df, before)
    assert isinstance(a.index, pd.RangeIndex)


def test_bad_input():
    df, _ = _panel(n_tickers=3, n_days=10)
    with pytest.raises(ValueError):
        iforest_scores(df.drop(columns=["vol_z"]))
    with pytest.raises(ValueError):
        iforest_scores(df, train_days=0)
    with pytest.raises(ValueError):
        iforest_scores(df, refit_every=True)
    with pytest.raises(ValueError):
        iforest_scores(df, components=[])
    with pytest.raises(ValueError):
        iforest_scores(df, components=["vol_z", "vol_z"])
    with pytest.raises(ValueError):
        iforest_scores(pd.concat([df, df.iloc[:1]]))


def test_int64_buckets_with_na():
    # build_features gives liq_bucket as Int64 with pd.NA during warm-up; that must not crash.
    df, dates = _panel()
    df["liq_bucket"] = pd.array([1] * len(df), dtype="Int64")
    df.loc[df["date"] == dates[0], "liq_bucket"] = pd.NA
    out = iforest_scores(df)
    ref = iforest_scores(df.assign(liq_bucket=df["liq_bucket"].astype("float64")))
    pd.testing.assert_frame_equal(out, ref)
    assert out["score"].notna().any()
