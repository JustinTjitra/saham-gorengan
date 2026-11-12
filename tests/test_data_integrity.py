"""Checks on the CSV files themselves. A failure here means the data is wrong."""

import re
from collections import defaultdict
from datetime import timedelta

import pytest

from saham_gorengan import (
    load_cases,
    load_court_named,
    load_excluded,
    load_regimes,
    load_windows,
)

TICKER = re.compile(r"^[A-Z]{4}$")


@pytest.fixture(scope="module")
def cases():
    return load_cases()


@pytest.fixture(scope="module")
def windows():
    return load_windows()


@pytest.fixture(scope="module")
def regimes():
    return load_regimes()


def test_ids_are_unique(cases, windows):
    assert len({c.case_id for c in cases}) == len(cases)
    assert len({w.window_id for w in windows}) == len(windows)


def test_tickers_are_four_uppercase_letters(cases, windows):
    for c in cases:
        for t in c.tickers:
            assert TICKER.match(t), (c.case_id, t)
    for w in windows:
        assert TICKER.match(w.ticker), w.window_id
    for row in load_court_named():
        assert TICKER.match(row.ticker), row
    for row in load_excluded():
        assert row.ticker == "" or TICKER.match(row.ticker), row


def test_every_window_belongs_to_a_case_and_matches_it(cases, windows):
    by_id = {c.case_id: c for c in cases}
    for w in windows:
        case = by_id[w.case_id]
        assert w.ticker in case.tickers, w.window_id
        assert w.label_class == case.label_class, w.window_id


def test_every_case_ticker_has_a_window(cases, windows):
    covered = {(w.case_id, w.ticker) for w in windows}
    for c in cases:
        for t in c.tickers:
            assert (c.case_id, t) in covered, (c.case_id, t)


def test_window_dates_are_ordered(windows):
    for w in windows:
        assert w.start <= w.end, w.window_id


def test_month_precision_windows_span_whole_months(windows):
    for w in windows:
        if w.precision == "month":
            assert w.start.day == 1, w.window_id
            assert (w.end + timedelta(days=1)).day == 1, w.window_id


def test_windows_of_one_case_and_ticker_do_not_overlap(windows):
    groups = defaultdict(list)
    for w in windows:
        groups[(w.case_id, w.ticker)].append(w)
    for ws in groups.values():
        ws.sort(key=lambda w: w.start)
        for a, b in zip(ws, ws[1:]):
            assert a.end < b.start, (a.window_id, b.window_id)


def test_alleged_cases_are_not_marked_sanctioned(cases):
    for c in cases:
        if c.label_class == "alleged":
            assert c.status in {"referred_to_prosecutor", "under_investigation"}, c.case_id
        else:
            assert c.status == "sanctioned", c.case_id


def test_excluded_tickers_never_appear_as_labels(windows):
    excluded = {e.ticker for e in load_excluded() if e.ticker}
    labelled = {w.ticker for w in windows}
    assert not excluded & labelled


def test_court_named_rows_are_unique():
    rows = load_court_named()
    assert len({(r.ticker, r.scandal) for r in rows}) == len(rows)


def test_regimes_are_contiguous_and_only_the_last_is_open(regimes):
    spans = []
    for rid in dict.fromkeys(r.regime_id for r in regimes):
        tiers = [r for r in regimes if r.regime_id == rid]
        assert len({(t.effective_from, t.effective_to) for t in tiers}) == 1, rid
        spans.append((rid, tiers[0].effective_from, tiers[0].effective_to))
    spans.sort(key=lambda s: s[1])
    for (rid_a, _, end_a), (rid_b, start_b, _) in zip(spans, spans[1:]):
        assert end_a is not None, rid_a
        assert end_a + timedelta(days=1) == start_b, (rid_a, rid_b)
    assert spans[-1][2] is None


def test_each_regime_covers_every_price_exactly_once(regimes):
    for rid in dict.fromkeys(r.regime_id for r in regimes):
        tiers = sorted((r for r in regimes if r.regime_id == rid), key=lambda r: r.price_gt)
        assert tiers[0].price_gt == 0, rid
        for a, b in zip(tiers, tiers[1:]):
            assert a.price_lte == b.price_gt, rid
        assert tiers[-1].price_lte is None, rid


def test_limits_are_plausible_percentages(regimes):
    for r in regimes:
        assert 0 < r.ara_pct <= 35
        assert 0 < r.arb_pct <= 35
