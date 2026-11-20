"""Market events: halts and structural breaks. Reads data/market_events.csv only."""

import csv
from datetime import date

import pytest

from saham_gorengan import MarketEvent, events_between, load_market_events
from saham_gorengan._load import data_dir

HEADER = ["date", "event_type", "scope", "description", "confidence", "source_url", "notes"]
EVENT_TYPES = {"trading_halt", "structural_break", "rule_change"}
SCOPES = {"market", "regular_board", "watchlist_board", "all_boards"}
HALT_DATES = {
    date(2020, 3, 12), date(2020, 3, 13), date(2020, 3, 17), date(2020, 3, 19),
    date(2020, 3, 23), date(2020, 3, 30), date(2020, 9, 10), date(2025, 3, 18),
    date(2025, 4, 8), date(2026, 1, 28), date(2026, 1, 29), date(2026, 10, 16),
}


@pytest.fixture(scope="module")
def events():
    return load_market_events()


def test_loads_and_enums_valid(events):
    assert events and all(isinstance(e, MarketEvent) for e in events)
    for e in events:
        assert e.event_type in EVENT_TYPES, e
        assert e.scope in SCOPES, e
        assert e.confidence in {"A", "B", "C"}, e
        assert e.description.strip() and e.source_url.startswith("https://"), e


def test_sorted_unique_dates_per_type(events):
    assert [e.date for e in events] == sorted(e.date for e in events)
    keys = [(e.date, e.event_type, e.scope) for e in events]
    assert len(set(keys)) == len(keys)


def test_events_between_inclusive():
    found = events_between(date(2026, 1, 28), date(2026, 1, 29), types={"trading_halt"})
    assert len(found) == 2
    assert [e.date for e in found] == [date(2026, 1, 28), date(2026, 1, 29)]


def test_known_halt_present():
    assert any(
        e.date == date(2025, 4, 8) and e.event_type == "trading_halt" for e in load_market_events()
    )


def test_halt_dates_match_research(events):
    assert {e.date for e in events if e.event_type == "trading_halt"} == HALT_DATES


def test_csv_header_and_every_row_has_seven_fields():
    with open(data_dir() / "market_events.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[0] == HEADER
    for row in rows[1:]:
        assert len(row) == 7, row


def test_events_between_rejects_reversed_range():
    with pytest.raises(ValueError):
        events_between(date(2026, 1, 2), date(2026, 1, 1))


def test_events_between_rejects_unknown_type():
    with pytest.raises(ValueError, match="bogus"):
        events_between(date(2026, 1, 1), date(2026, 12, 31), types={"bogus"})


def test_bad_enum_names_the_row():
    from saham_gorengan.events import _event

    row = {
        "date": "2026-01-28", "event_type": "halt", "scope": "market",
        "description": "x", "confidence": "B", "source_url": "https://e.x", "notes": "",
    }
    with pytest.raises(ValueError, match="2026-01-28"):
        _event(row)
