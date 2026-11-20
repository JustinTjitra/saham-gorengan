"""Yahoo Finance daily source (via yfinance, imported lazily)."""
from __future__ import annotations

import logging
import re
import time
from datetime import date, timedelta
from typing import Callable, Sequence

import pandas as pd

from saham_gorengan.bars import PRICES, empty_bars, validate_bars
from saham_gorengan.sources.base import SourceError

log = logging.getLogger(__name__)

_TICKER = re.compile(r"[A-Z]{4}")
_FIELDS = {"Open": "open", "High": "high", "Low": "low", "Close": "close",
           "Adj Close": "adj_close", "Volume": "volume"}


def _retryable(exc: BaseException) -> bool:
    return "RateLimit" in type(exc).__name__ or isinstance(exc, ConnectionError)


class YahooSource:
    name = "yahoo"

    def __init__(self, max_retries: int = 5, base_delay: float = 2.0,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._sleep = sleep

    def fetch(self, tickers: Sequence[str], start: date, end: date) -> pd.DataFrame:
        clean = [t.strip().upper() for t in tickers]
        bad = [t for t in clean if not _TICKER.fullmatch(t)]
        if bad:
            raise ValueError(f"tickers not matching ^[A-Z]{{4}}$: {bad}")
        if start > end:
            raise ValueError(f"start {start} is after end {end}")
        try:
            import yfinance
        except ImportError as exc:
            raise SourceError("pip install saham-gorengan[yahoo]") from exc
        if not clean:
            return empty_bars()

        symbols = [f"{t}.JK" for t in clean]
        raw = self._download(yfinance, symbols, start, end + timedelta(days=1))
        frames = self._split(raw, clean)
        parts = []
        for t in clean:
            part = frames.get(t)
            if part is not None:
                part = part.dropna(how="all", subset=PRICES)
            if part is None or part.empty:
                log.info("yahoo: no data for %s", t)
                continue
            parts.append(part.assign(ticker=t))
        if not parts:
            return validate_bars(empty_bars())
        bars = pd.concat(parts, ignore_index=True)
        bars["source"] = self.name
        return validate_bars(bars)

    def _download(self, yf, symbols: list[str], start: date, end: date) -> pd.DataFrame:
        attempt = 0
        while True:
            try:
                return yf.download(symbols, start=start, end=end, interval="1d",
                                   auto_adjust=False, actions=False, group_by="ticker",
                                   progress=False, threads=False)
            except Exception as exc:
                if not _retryable(exc):
                    raise
                if attempt >= self.max_retries:
                    raise SourceError(
                        f"yahoo: giving up after {self.max_retries} retries: {exc}") from exc
                self._sleep(self.base_delay * 2 ** attempt)
                attempt += 1

    @staticmethod
    def _split(raw: pd.DataFrame, tickers: list[str]) -> dict[str, pd.DataFrame]:
        """Per-ticker frames with canonical column names and a ``date`` column."""
        if raw is None or raw.empty:
            return {}
        idx = pd.DatetimeIndex(raw.index)
        if idx.tz is not None:
            idx = idx.tz_convert("Asia/Jakarta").tz_localize(None)
        dates = idx.normalize()

        def build(df: pd.DataFrame) -> pd.DataFrame:
            out = df[[c for c in _FIELDS if c in df.columns]].rename(columns=_FIELDS)
            out = out.reset_index(drop=True)
            out.insert(0, "date", dates)
            return out

        if isinstance(raw.columns, pd.MultiIndex):
            if set(raw.columns.get_level_values(0)) <= set(_FIELDS):  # (field, symbol) layout
                raw = raw.swaplevel(axis=1)
            res = {}
            for sym in raw.columns.get_level_values(0).unique():
                t = str(sym).removesuffix(".JK")
                res[t] = build(raw[sym])
            return res
        if len(tickers) != 1:
            raise SourceError("yahoo: flat columns returned for multiple tickers")
        return {tickers[0]: build(raw)}
