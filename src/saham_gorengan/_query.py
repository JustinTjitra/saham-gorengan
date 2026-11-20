"""Lookups over the loaded data."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from ._load import BOARDS, CONFIDENCES, LABEL_CLASSES, PRECISIONS, Window, _regimes, _windows


@dataclass(frozen=True)
class PriceLimits:
    regime_id: str
    ara_pct: int | None
    arb_pct: int | None
    ara_fixed_idr: int | None
    arb_fixed_idr: int | None

    def upper(self, reference_price: float) -> float:
        """Auto-rejection-above price: ref*(1+ara_pct/100) or ref+ara_fixed_idr. Not tick-rounded."""
        if self.ara_pct is not None:
            return reference_price * (1 + self.ara_pct / 100)
        return reference_price + self.ara_fixed_idr

    def lower(self, reference_price: float) -> float:
        """Auto-rejection-below price: ref*(1-arb_pct/100) or ref-arb_fixed_idr. Not tick-rounded."""
        if self.arb_pct is not None:
            return reference_price * (1 - self.arb_pct / 100)
        return reference_price - self.arb_fixed_idr


def price_limits(day: date, reference_price: float, board: str = "regular") -> PriceLimits:
    """Auto-rejection limits for a share on ``board`` on ``day``.

    ``reference_price`` is the price the limit is measured from (normally the
    previous close); it also picks the price tier. ``board`` is one of
    ``BOARDS``; "regular" covers the main, development and new economy boards.
    Only tiers present in the data are considered, so a board with no rows
    raises ValueError.
    """
    if board not in BOARDS:
        raise ValueError(f"unknown board {board!r}; use {sorted(BOARDS)}")
    if reference_price <= 0:
        raise ValueError(f"reference_price must be positive, got {reference_price}")
    tiers = [t for t in _regimes() if t.board == board]
    if not tiers:
        raise ValueError(f"no regimes in the data for board {board!r}")
    first = min(t.effective_from for t in tiers)
    if day < first:
        raise ValueError(f"{day} is before the first {board} regime in the data ({first})")
    for t in tiers:
        in_period = t.effective_from <= day and (t.effective_to is None or day <= t.effective_to)
        in_tier = t.price_gt < reference_price and (t.price_lte is None or reference_price <= t.price_lte)
        if in_period and in_tier:
            return PriceLimits(t.regime_id, t.ara_pct, t.arb_pct, t.ara_fixed_idr, t.arb_fixed_idr)
    raise LookupError(f"no {board} regime tier for {day} at price {reference_price}")  # data bug


def labels_on(
    ticker: str,
    day: date,
    classes: Iterable[str] = ("sanctioned",),
    precisions: Iterable[str] = ("day", "month", "year"),
    min_confidence: str = "C",
) -> list[Window]:
    """Manipulation windows covering ``ticker`` on ``day`` (bounds inclusive).

    Defaults to sanctioned cases only; pass ``classes={"sanctioned", "alleged"}``
    to include cases still on the criminal track. ``precisions={"day"}`` drops
    windows that OJK stated only to the month or year. ``min_confidence`` keeps
    windows at that tier or better (A > B > C).
    """
    classes, precisions = set(classes), set(precisions)
    if bad := classes - LABEL_CLASSES:
        raise ValueError(f"unknown classes {sorted(bad)}; use {sorted(LABEL_CLASSES)}")
    if bad := precisions - PRECISIONS:
        raise ValueError(f"unknown precisions {sorted(bad)}; use {sorted(PRECISIONS)}")
    if min_confidence not in CONFIDENCES:
        raise ValueError(f"min_confidence must be one of {CONFIDENCES}")
    allowed = set(CONFIDENCES[: CONFIDENCES.index(min_confidence) + 1])
    ticker = ticker.upper()
    return [
        w for w in _windows()
        if w.ticker == ticker
        and w.covers(day)
        and w.label_class in classes
        and w.precision in precisions
        and w.confidence in allowed
    ]
