"""Ticker-day label panel built from data/windows.csv.

This is a LABEL, not a feature: it is built from the whole windows table, which
was curated after the fact (OJK/court findings). It must never be used as a
detector input or in any score for day D. Evaluation joins detector scores onto it.
"""
from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from ._load import CONFIDENCES, LABEL_CLASSES, PRECISIONS, _windows
from .bars import validate_bars


def label_panel(
    bars: pd.DataFrame,
    classes: Iterable[str] = ("sanctioned", "convicted"),
    precisions: Iterable[str] = ("day", "month", "year"),
    min_confidence: str = "C",
) -> pd.DataFrame:
    """One label per (date, ticker) row of ``bars``, filtered like ``labels_on()``.

    Columns: date, ticker, label ("boolean", never NA), n_windows (Int64),
    window_id, label_class, confidence (string; NA when label is False). Same rows
    and order as ``validate_bars(bars)``. When several windows cover a row, the
    details come from the best confidence, then earliest start, then smallest window_id.
    """
    out = validate_bars(bars)
    # Same checks and messages as labels_on() in _query.py (inline there, so duplicated).
    classes, precisions = set(classes), set(precisions)
    if bad := classes - LABEL_CLASSES:
        raise ValueError(f"unknown classes {sorted(bad)}; use {sorted(LABEL_CLASSES)}")
    if bad := precisions - PRECISIONS:
        raise ValueError(f"unknown precisions {sorted(bad)}; use {sorted(PRECISIONS)}")
    if min_confidence not in CONFIDENCES:
        raise ValueError(f"min_confidence must be one of {CONFIDENCES}")
    allowed = set(CONFIDENCES[: CONFIDENCES.index(min_confidence) + 1])

    chosen = sorted(
        (w for w in _windows()
         if w.label_class in classes and w.precision in precisions and w.confidence in allowed),
        key=lambda w: (CONFIDENCES.index(w.confidence), w.start, w.window_id),
    )
    n = len(out)
    counts = pd.Series(0, index=out.index, dtype="int64")
    assigned = pd.Series(False, index=out.index)
    details = {k: pd.Series(pd.NA, index=out.index, dtype="string")
               for k in ("window_id", "label_class", "confidence")}
    for w in chosen:  # best window first; first cover wins the details
        covered = (out["ticker"] == w.ticker) & (out["date"] >= pd.Timestamp(w.start)) \
            & (out["date"] <= pd.Timestamp(w.end))
        covered = covered.fillna(False).to_numpy(dtype=bool) if n else covered.to_numpy(dtype=bool)
        counts += covered
        first = covered & ~assigned.to_numpy()
        for k, v in (("window_id", w.window_id), ("label_class", w.label_class),
                     ("confidence", w.confidence)):
            details[k][first] = v
        assigned |= covered

    return pd.DataFrame({
        "date": out["date"],
        "ticker": out["ticker"],
        "label": (counts > 0).astype("boolean"),
        "n_windows": counts.astype("Int64"),
        **details,
    }).reset_index(drop=True)
