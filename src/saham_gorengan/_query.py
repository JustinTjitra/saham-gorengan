"""Lookups over the loaded data."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from ._load import CONFIDENCES, LABEL_CLASSES, PRECISIONS, Window, _regimes, _windows


@dataclass(frozen=True)
class PriceLimits:
    ara_pct: int
    arb_pct: int
    regime_id: str


def price_limits(day: date, reference_price: float) -> PriceLimits:
    """Auto-rejection limits for a regular-market share on ``day``.

    ``reference_price`` is the price the limit is measured from (normally the
    previous close); it also picks the price tier. Covers the main and
    development boards only: the Acceleration Board and full-call-auction
    watchlist stocks have their own limits, which are not in this dataset.
    """
    if reference_price <= 0:
        raise ValueError(f"reference_price must be positive, got {reference_price}")
    tiers = _regimes()
    first = min(t.effective_from for t in tiers)
    if day < first:
        raise ValueError(f"{day} is before the first regime in the data ({first})")
    for t in tiers:
        in_period = t.effective_from <= day and (t.effective_to is None or day <= t.effective_to)
        in_tier = t.price_gt < reference_price and (t.price_lte is None or reference_price <= t.price_lte)
        if in_period and in_tier:
            return PriceLimits(t.ara_pct, t.arb_pct, t.regime_id)
    raise LookupError(f"no regime tier for {day} at price {reference_price}")  # data bug


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
