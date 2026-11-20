"""Deterministic synthetic daily panels with injected pump-and-dump episodes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from string import ascii_uppercase
from typing import Sequence

import numpy as np
import pandas as pd

from .bars import validate_bars

MAX_TICKERS = 26 * 26


@dataclass(frozen=True)
class Pump:
    ticker: str
    start: date  # first pump day (inclusive)
    pump_days: int = 10
    daily_return: float = 0.15  # mean return per pump day
    volume_mult: float = 8.0  # volume multiplier during the pump and dump
    dump_days: int = 5
    dump_return: float = -0.12


def _ticker(i: int) -> str:
    return "SY" + ascii_uppercase[i // 26] + ascii_uppercase[i % 26]


def _windows(pumps: Sequence[Pump], tickers: list[str], days: pd.DatetimeIndex) -> dict:
    """Map ticker -> list of (pump, first row index), validated."""
    out: dict[str, list[tuple[Pump, int]]] = {}
    for p in pumps:
        if p.ticker not in tickers:
            raise ValueError(f"pump ticker {p.ticker!r} is not generated")
        pos = days.searchsorted(pd.Timestamp(p.start))
        if pos >= len(days) or days[pos] != pd.Timestamp(p.start):
            raise ValueError(f"pump start {p.start} is not a trading day in range")
        if pos + p.pump_days + p.dump_days > len(days):
            raise ValueError(f"pump on {p.ticker} from {p.start} runs past the last trading day")
        for q, qpos in out.get(p.ticker, []):
            if pos < qpos + q.pump_days + q.dump_days and qpos < pos + p.pump_days + p.dump_days:
                raise ValueError(f"overlapping pumps on {p.ticker}")
        out.setdefault(p.ticker, []).append((p, pos))
    return out


def synthetic_bars(n_tickers: int = 20, start: date = date(2022, 1, 3), end: date = date(2022, 12, 30),
                   seed: int = 0, pumps: Sequence[Pump] = ()) -> pd.DataFrame:
    if not 1 <= n_tickers <= MAX_TICKERS:
        raise ValueError(f"n_tickers must be in [1, {MAX_TICKERS}], got {n_tickers}")
    days = pd.bdate_range(start, end)
    n = len(days)
    tickers = [_ticker(i) for i in range(n_tickers)]
    windows = _windows(pumps, tickers, days)
    rng = np.random.default_rng(seed)

    frames = []
    for tk in tickers:
        ret = rng.normal(0.0, 0.02, n)
        vol_mult = np.ones(n)
        for p, pos in windows.get(tk, []):
            a, b = pos + p.pump_days, pos + p.pump_days + p.dump_days
            ret[pos:a] += p.daily_return
            ret[a:b] += p.dump_return
            vol_mult[pos:b] = p.volume_mult
        close = rng.uniform(100, 2000) * np.exp(np.cumsum(ret))
        prev = np.concatenate([[close[0] / np.exp(ret[0])], close[:-1]])
        open_ = prev * (1 + rng.normal(0.0, 0.005, n))
        high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0.0, 0.005, n)))
        low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0.0, 0.005, n)))
        o, h, l, c = (np.maximum(np.round(x), 1.0) for x in (open_, high, low, close))
        h = np.max([o, h, l, c], axis=0)
        l = np.min([o, h, l, c], axis=0)
        volume = np.round(rng.uniform(1e5, 1e7) * rng.lognormal(0.0, 0.4, n) * vol_mult)
        frames.append(pd.DataFrame({
            "date": days, "ticker": tk, "open": o, "high": h, "low": l, "close": c,
            "volume": volume, "value": c * volume,
            "frequency": pd.array(np.round(volume / 500), dtype="Int64"),
            "source": "synthetic",
        }))
    return validate_bars(pd.concat(frames, ignore_index=True))
