"""Common interface for daily-bar data sources."""
from __future__ import annotations

from datetime import date
from typing import Protocol, Sequence

import pandas as pd


class SourceError(RuntimeError):
    """A source could not deliver data (missing dependency, retries exhausted, ...)."""


class DailySource(Protocol):
    name: str

    def fetch(self, tickers: Sequence[str], start: date, end: date) -> pd.DataFrame:
        """Return daily bars for ``tickers`` over [start, end] in the canonical bars schema."""
        ...
