"""Tick-size table: boundaries, rounding and table integrity."""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, timedelta

import pytest

import saham_gorengan
from saham_gorengan import TickBand, load_tick_sizes, round_to_tick, tick_size
from saham_gorengan._load import data_dir

D2024 = date(2024, 6, 3)
D2015 = date(2015, 1, 2)


@pytest.mark.parametrize("price,tick", [
    (199, 1), (200, 2), (499, 2), (500, 5), (1999, 5), (2000, 10), (4999, 10), (5000, 25),
])
def test_boundaries_2024(price, tick):
    assert tick_size(D2024, price) == tick


@pytest.mark.parametrize("price,tick", [(499, 1), (500, 5), (5000, 25)])
def test_boundaries_2014_period(price, tick):
    assert tick_size(D2015, price) == tick


def test_period_edges():
    assert tick_size(date(2016, 5, 1), 300) == 1
    assert tick_size(date(2016, 5, 2), 300) == 2
    assert tick_size(date(2014, 1, 6), 300) == 1


def test_rounding():
    assert round_to_tick(203, D2024, "down") == 202
    assert round_to_tick(203, D2024, "up") == 204
    assert round_to_tick(5012, D2024, "nearest") == 5000
    assert round_to_tick(5013, D2024, "nearest") == 5025
    assert round_to_tick(203, D2024, "nearest") == 204  # tie resolves upward
    assert round_to_tick(1999.5, D2024, "up") == 2000
    assert isinstance(round_to_tick(203, D2024), int)


def test_rounded_price_is_on_its_own_grid():
    for mode in ("down", "up", "nearest"):
        for p in (0.4, 1, 199.5, 200.5, 499.5, 1999.5, 4999.5, 5000.5, 12345.6):
            r = round_to_tick(p, D2024, mode)
            assert r % tick_size(D2024, max(r, 1)) == 0 or r == 0


def test_before_coverage_raises():
    with pytest.raises(ValueError, match="before"):
        tick_size(date(2013, 12, 31), 100)
    with pytest.raises(ValueError, match="before"):
        round_to_tick(100, date(2010, 1, 1))


def test_bad_arguments():
    for bad in (0, -5):
        with pytest.raises(ValueError):
            tick_size(D2024, bad)
        with pytest.raises(ValueError):
            round_to_tick(bad, D2024)
    with pytest.raises(ValueError):
        round_to_tick(100, D2024, "sideways")


def test_exports():
    for name in ("TickBand", "load_tick_sizes", "tick_size", "round_to_tick"):
        assert name in saham_gorengan.__all__


def test_csv_shape():
    with open(data_dir() / "tick_sizes.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["band_id", "effective_from", "effective_to", "price_gte", "price_lt",
                       "tick_idr", "decree", "source_url", "notes"]
    assert all(len(r) == 9 for r in rows)


def test_integrity_contiguous():
    bands = load_tick_sizes()
    assert all(isinstance(b, TickBand) for b in bands)
    assert all(b.source_url for b in bands)
    periods = defaultdict(list)
    for b in bands:
        periods[(b.effective_from, b.effective_to)].append(b)
    ordered = sorted(periods)
    for key in ordered:
        group = sorted(periods[key], key=lambda b: b.price_gte)
        assert group[0].price_gte == 0
        assert group[-1].price_lt is None
        for lo, hi in zip(group, group[1:]):
            assert lo.price_lt == hi.price_gte
    for (_, end), (start, _) in zip(ordered, ordered[1:]):
        assert end is not None and end + timedelta(days=1) == start
    assert ordered[0][0] == date(2014, 1, 6)
    assert ordered[-1][1] is None
