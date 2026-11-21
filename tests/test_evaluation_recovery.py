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
