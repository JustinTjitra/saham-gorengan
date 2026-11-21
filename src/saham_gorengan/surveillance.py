"""IDX surveillance events (UMA, suspensions, notations, watchlist moves, investigations).

These are weak labels, not ground truth. A UMA notice "does not always violate
regulations": it flags a price or volume extreme after the fact and is not a finding
of wrongdoing. Suspension reasons are classified from announcement text with the rules
in `classify_suspension_reason`. See research_notes/IDX manipulation detector sources/surveillance_weak_labels.md
(sections 1-3; the reason phrases are in section 2, "Inferences").

The event data lives in the private data store, so the loader takes a path.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

HEADER = ["date", "ticker", "event_type", "reason_class", "source", "source_url", "notes"]
EVENT_TYPES = frozenset({
    "uma", "suspension", "suspension_lifted", "notation",
    "watchlist_entry", "watchlist_exit", "investigation",
})
REASON_CLASSES = frozenset({
    "price_up", "price_down", "cooling_down", "late_filing", "listing_fee",
    "free_float", "going_concern", "non_price_other", "unknown",
})
SOURCES = frozenset({"idx_announcement", "news", "manual"})

_TICKER = re.compile(r"^[A-Z]{4}$")
_I_A = re.compile(r"\bi-a\b")


@dataclass(frozen=True)
class SurveillanceEvent:
    date: date
    ticker: str
    event_type: str
    reason_class: str | None  # set only for event_type == "suspension"; None otherwise
    source: str
    source_url: str
    notes: str


def _check(value: str, allowed: frozenset[str], field: str, where: str) -> None:
    if value not in allowed:
        raise ValueError(f"{where}: {field}={value!r} not in {sorted(allowed)}")


def load_surveillance_events(path: str | Path) -> list[SurveillanceEvent]:
    """Events from a CSV at `path`, sorted by (date, ticker, event_type).

    Raises ValueError naming the 1-based line number (header is line 1) on any bad row.
    """
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != HEADER:
            raise ValueError(f"line 1: header {reader.fieldnames!r} != {HEADER!r}")
        events: list[SurveillanceEvent] = []
        seen: dict[tuple[date, str, str], int] = {}
        for r in reader:
            where = f"line {reader.line_num}"
            if None in r or any(v is None for v in r.values()):
                raise ValueError(f"{where}: expected {len(HEADER)} fields")
            _check(r["event_type"], EVENT_TYPES, "event_type", where)
            _check(r["source"], SOURCES, "source", where)
            if not _TICKER.match(r["ticker"]):
                raise ValueError(f"{where}: ticker={r['ticker']!r} does not match ^[A-Z]{{4}}$")
            if not r["source_url"].strip():
                raise ValueError(f"{where}: source_url is empty")
            try:
                day = date.fromisoformat(r["date"])
            except ValueError:
                raise ValueError(f"{where}: bad date {r['date']!r}") from None
            reason: str | None = r["reason_class"] or None
            if r["event_type"] == "suspension":
                if reason is None:
                    raise ValueError(f"{where}: reason_class is blank on a suspension row")
                _check(reason, REASON_CLASSES, "reason_class", where)
            elif reason is not None:
                raise ValueError(f"{where}: reason_class={reason!r} set on a {r['event_type']} row")
            key = (day, r["ticker"], r["event_type"])
            if key in seen:
                raise ValueError(f"{where}: duplicate of line {seen[key]} {key}")
            seen[key] = reader.line_num
            events.append(SurveillanceEvent(
                date=day,
                ticker=r["ticker"],
                event_type=r["event_type"],
                reason_class=reason,
                source=r["source"],
                source_url=r["source_url"],
                notes=r["notes"],
            ))
    return sorted(events, key=lambda e: (e.date, e.ticker, e.event_type))


def classify_suspension_reason(text: str) -> str:
    """Classify announcement text into a REASON_CLASSES member (first matching rule wins)."""
    t = " ".join(text.split()).lower()
    if not t:
        return "unknown"
    if "peningkatan harga kumulatif" in t:
        return "price_up"
    if "penurunan harga kumulatif" in t:
        return "price_down"
    if "cooling down" in t:
        return "cooling_down"
    if "laporan keuangan" in t or "keterlambatan" in t:
        return "late_filing"
    if "biaya pencatatan" in t:
        return "listing_fee"
    if "free float" in t or _I_A.search(t):
        return "free_float"
    if "going concern" in t or "kelangsungan usaha" in t:
        return "going_concern"
    return "non_price_other"
