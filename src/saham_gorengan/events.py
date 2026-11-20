"""Dated market-wide trading halts, structural breaks and rule changes (IDX)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from functools import lru_cache

from ._load import CONFIDENCES, _check, _rows

EVENT_TYPES = frozenset({"trading_halt", "structural_break", "rule_change"})
SCOPES = frozenset({"market", "regular_board", "watchlist_board", "all_boards"})


@dataclass(frozen=True)
class MarketEvent:
    date: date
    event_type: str
    scope: str
    description: str
    confidence: str
    source_url: str
    notes: str


def _event(r: dict[str, str]) -> MarketEvent:
    row_id = f"{r['date']} {r['event_type']}"
    _check(r["event_type"], EVENT_TYPES, "event_type", row_id)
    _check(r["scope"], SCOPES, "scope", row_id)
    _check(r["confidence"], CONFIDENCES, "confidence", row_id)
    for field in ("description", "source_url"):
        if not r[field].strip():
            raise ValueError(f"{row_id}: {field} is empty")
    return MarketEvent(
        date=date.fromisoformat(r["date"]),
        event_type=r["event_type"],
        scope=r["scope"],
        description=r["description"],
        confidence=r["confidence"],
        source_url=r["source_url"],
        notes=r["notes"],
    )


@lru_cache(maxsize=None)
def _events() -> tuple[MarketEvent, ...]:
    return tuple(sorted((_event(r) for r in _rows("market_events.csv")), key=lambda e: e.date))


def load_market_events() -> list[MarketEvent]:
    """Every halt and structural break in the research notes, sorted by date."""
    return list(_events())


def events_between(start: date, end: date, types: Iterable[str] | None = None) -> list[MarketEvent]:
    """Events dated from start to end (both inclusive), sorted by date.

    `types` keeps only the given event_type values. Unknown types raise ValueError.
    """
    if start > end:
        raise ValueError(f"start {start} is after end {end}")
    wanted = None
    if types is not None:
        wanted = frozenset(types)
        unknown = wanted - EVENT_TYPES
        if unknown:
            raise ValueError(f"unknown event types {sorted(unknown)}; expected {sorted(EVENT_TYPES)}")
    return [
        e for e in _events()
        if start <= e.date <= end and (wanted is None or e.event_type in wanted)
    ]
