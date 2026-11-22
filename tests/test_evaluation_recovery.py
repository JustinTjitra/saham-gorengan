import time
from datetime import date

import pytest

from saham_gorengan.evaluation.recovery import run_recovery


def test_composite_recovers():
    assert run_recovery(seed=0)["composite"] >= 0.8


def test_baselines_recover():
    r = run_recovery(seed=0)
    assert r["rank_ret"] >= 0.8
    assert r["rank_vol"] >= 0.8


def test_deterministic():
    assert run_recovery(seed=1) == run_recovery(seed=1)


def test_runtime():
    t0 = time.perf_counter()
    run_recovery(seed=2)
    assert time.perf_counter() - t0 < 60


def test_bad_dates():
    with pytest.raises(ValueError):
        run_recovery(start=date(2024, 1, 2), end=date(2024, 3, 29))


def test_too_many_pumps():
    with pytest.raises(ValueError):
        run_recovery(n_tickers=3, n_pumps=4)


def test_defaults_unchanged():
    assert run_recovery(seed=0) == {"rank_ret": 1.0, "rank_vol": 1.0, "rank_rule": 1.0, "composite": 1.0}


def test_include_random_adds_key():
    r = run_recovery(seed=0, include_random=True, n_tickers=30, n_pumps=3)
    assert "random" in r and 0.0 <= r["random"] <= 1.0


_SWEEP_SECONDS = {}


@pytest.fixture(scope="module")
def sweep():
    from saham_gorengan.evaluation.recovery import recovery_sweep

    t0 = time.perf_counter()
    df = recovery_sweep()
    _SWEEP_SECONDS["t"] = time.perf_counter() - t0
    return df


def _cell(df, dr, vm):
    sub = df[(df.daily_return == dr) & (df.volume_mult == vm)]
    return dict(zip(sub.detector, sub.recall))


def test_sweep_shape(sweep):
    assert list(sweep.columns) == ["daily_return", "volume_mult", "detector", "recall"]
    assert len(sweep) == 40
    assert set(sweep.detector) == {"rank_ret", "rank_vol", "rank_rule", "composite", "random"}


def test_strong_cell(sweep):
    assert _cell(sweep, 0.15, 8.0)["composite"] >= 0.9


def test_beats_random_when_strong(sweep):
    c = _cell(sweep, 0.15, 8.0)
    for d in ("rank_ret", "rank_vol", "rank_rule", "composite"):
        assert c[d] - c["random"] >= 0.3 - 1e-9, (d, c)


def test_monotone_composite(sweep):
    def m(dr):
        s = sweep[(sweep.daily_return == dr) & (sweep.detector == "composite")]
        return s.recall.mean()
    assert m(0.15) >= m(0.005)


def test_sweep_runtime(sweep):
    assert _SWEEP_SECONDS["t"] < 120


def test_sweep_informative(sweep):
    comp = sweep[sweep.detector == "composite"]
    assert (comp.recall < 0.9).any()
