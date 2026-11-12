"""Read the CSV files in data/ into frozen dataclasses."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

LABEL_CLASSES = frozenset({"sanctioned", "alleged"})
STATUSES = frozenset({"sanctioned", "referred_to_prosecutor", "under_investigation"})
PRECISIONS = frozenset({"day", "month", "year"})
CONFIDENCES = ("A", "B", "C")  # best first


def data_dir() -> Path:
    """Folder holding the CSVs: inside the installed package, else the repo root."""
    packaged = Path(__file__).parent / "data"
    if packaged.is_dir():
        return packaged
    return Path(__file__).resolve().parents[2] / "data"


def _rows(name: str) -> list[dict[str, str]]:
    with open(data_dir() / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _date(s: str) -> date | None:
    return date.fromisoformat(s) if s else None


def _int(s: str) -> int | None:
    return int(s) if s else None


def _split(s: str) -> tuple[str, ...]:
    return tuple(p.strip() for p in s.split(";") if p.strip())


def _check(value: str, allowed, field: str, row_id: str) -> str:
    if value not in allowed:
        raise ValueError(f"{row_id}: {field}={value!r} not in {sorted(allowed)}")
    return value


@dataclass(frozen=True)
class Case:
    case_id: str
    tickers: tuple[str, ...]
    label_class: str
    status: str
    scheme: str
    articles: tuple[str, ...]
    parties: str
    fine_idr: int | None
    disgorgement_idr: int | None
    decision_date: date | None
    announcement_date: date
    release_no: str
    confidence: str
    source_urls: tuple[str, ...]
    notes: str


@dataclass(frozen=True)
class Window:
    window_id: str
    case_id: str
    ticker: str
    start: date
    end: date  # inclusive
    precision: str
    label_class: str
    confidence: str
    notes: str

    def covers(self, day: date) -> bool:
        return self.start <= day <= self.end


@dataclass(frozen=True)
class CourtNamed:
    ticker: str
    scandal: str
    named_by: str
    court_ref: str
    confidence: str
    source_url: str
    notes: str


@dataclass(frozen=True)
class Excluded:
    subject: str
    ticker: str
    violation: str
    sanction: str
    date: str  # YYYY-MM-DD, or YYYY-MM when only the month is known
    release_no: str
    source_url: str
    why_excluded: str


@dataclass(frozen=True)
class RegimeTier:
    regime_id: str
    effective_from: date
    effective_to: date | None  # inclusive; None = still in force as far as the source knows
    price_gt: int
    price_lte: int | None  # None = no upper bound
    ara_pct: int
    arb_pct: int
    decree: str
    source_url: str
    notes: str


@lru_cache(maxsize=None)
def _cases() -> tuple[Case, ...]:
    out = []
    for r in _rows("cases.csv"):
        cid = r["case_id"]
        out.append(Case(
            case_id=cid,
            tickers=_split(r["tickers"]),
            label_class=_check(r["label_class"], LABEL_CLASSES, "label_class", cid),
            status=_check(r["status"], STATUSES, "status", cid),
            scheme=r["scheme"],
            articles=_split(r["articles"]),
            parties=r["parties"],
            fine_idr=_int(r["fine_idr"]),
            disgorgement_idr=_int(r["disgorgement_idr"]),
            decision_date=_date(r["decision_date"]),
            announcement_date=date.fromisoformat(r["announcement_date"]),
            release_no=r["release_no"],
            confidence=_check(r["confidence"], CONFIDENCES, "confidence", cid),
            source_urls=_split(r["source_urls"]),
            notes=r["notes"],
        ))
    return tuple(out)


@lru_cache(maxsize=None)
def _windows() -> tuple[Window, ...]:
    out = []
    for r in _rows("windows.csv"):
        wid = r["window_id"]
        out.append(Window(
            window_id=wid,
            case_id=r["case_id"],
            ticker=r["ticker"],
            start=date.fromisoformat(r["start"]),
            end=date.fromisoformat(r["end"]),
            precision=_check(r["precision"], PRECISIONS, "precision", wid),
            label_class=_check(r["label_class"], LABEL_CLASSES, "label_class", wid),
            confidence=_check(r["confidence"], CONFIDENCES, "confidence", wid),
            notes=r["notes"],
        ))
    return tuple(out)


@lru_cache(maxsize=None)
def _court_named() -> tuple[CourtNamed, ...]:
    return tuple(
        CourtNamed(**{**r, "confidence": _check(r["confidence"], CONFIDENCES, "confidence", r["ticker"])})
        for r in _rows("court_named.csv")
    )


@lru_cache(maxsize=None)
def _excluded() -> tuple[Excluded, ...]:
    return tuple(Excluded(**r) for r in _rows("excluded.csv"))


@lru_cache(maxsize=None)
def _regimes() -> tuple[RegimeTier, ...]:
    return tuple(
        RegimeTier(
            regime_id=r["regime_id"],
            effective_from=date.fromisoformat(r["effective_from"]),
            effective_to=_date(r["effective_to"]),
            price_gt=int(r["price_gt"]),
            price_lte=_int(r["price_lte"]),
            ara_pct=int(r["ara_pct"]),
            arb_pct=int(r["arb_pct"]),
            decree=r["decree"],
            source_url=r["source_url"],
            notes=r["notes"],
        )
        for r in _rows("price_limit_regimes.csv")
    )


def load_cases() -> list[Case]:
    """One row per enforcement case (sanctioned or alleged)."""
    return list(_cases())


def load_windows() -> list[Window]:
    """One row per ticker manipulation window. Use these as labels."""
    return list(_windows())


def load_court_named() -> list[CourtNamed]:
    """Tickers named in the Jiwasraya and Asabri cases. No windows: not for window-based labels."""
    return list(_court_named())


def load_excluded() -> list[Excluded]:
    """Sanctioned cases that are NOT trading manipulation. Do not use as positive labels."""
    return list(_excluded())


def load_regimes() -> list[RegimeTier]:
    """ARA/ARB auto-rejection limits, one row per (regime, price tier)."""
    return list(_regimes())
