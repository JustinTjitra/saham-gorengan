"""Deterministic synthetic daily panels with injected pump-and-dump episodes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from string import ascii_uppercase
from typing import Callable, Sequence

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


def _check_dates(bars: pd.DataFrame, check_dates: Sequence[date] | None, n_checks: int) -> list[pd.Timestamp]:
    if check_dates is not None:
        return [pd.Timestamp(d) for d in check_dates]
    if n_checks < 1:
        raise ValueError(f"n_checks must be >= 1, got {n_checks}")
    days = np.sort(bars["date"].unique())
    days = days[int(len(days) * 0.2):]
    if len(days) == 0:
        raise ValueError("bars has no dates to check")
    idx = np.unique(np.round(np.linspace(0, len(days) - 1, n_checks)).astype(int))
    idx = np.union1d(idx, [len(days) - 1])
    return [pd.Timestamp(days[i]) for i in idx]


def _is_missing(v) -> bool:
    return v is None or v is pd.NA or v is pd.NaT or (isinstance(v, float) and v != v)


def _same(a, b, atol: float) -> bool:
    ma, mb = _is_missing(a), _is_missing(b)
    if ma or mb:
        return ma and mb
    num = (bool, int, float, np.bool_, np.integer, np.floating)
    if isinstance(a, num) and isinstance(b, num):
        return abs(float(a) - float(b)) <= atol
    return bool(a == b)


def _feature_frame(fn: Callable[[pd.DataFrame], pd.DataFrame], bars: pd.DataFrame) -> pd.DataFrame:
    out = fn(bars)
    missing = [c for c in ("date", "ticker") if c not in out.columns]
    if missing:
        raise ValueError(f"feature_fn output lacks column(s) {missing}")
    out = out.copy()
    out["date"] = pd.to_datetime(out["date"])
    out["ticker"] = out["ticker"].astype(str)
    if out.duplicated(["date", "ticker"]).any():
        raise ValueError("feature_fn output has duplicate (date, ticker) rows")
    return out


def assert_no_lookahead(feature_fn: Callable[[pd.DataFrame], pd.DataFrame], bars: pd.DataFrame,
                        check_dates: Sequence[date] | None = None, n_checks: int = 5,
                        atol: float = 1e-9) -> None:
    """Raise AssertionError if a feature for day D changes when data after D is removed."""
    dates = _check_dates(bars, check_dates, n_checks)
    full = _feature_frame(feature_fn, bars)
    for d in dates:
        trunc = _feature_frame(feature_fn, bars[bars["date"] <= d].copy())
        a = full[full["date"] == d].set_index("ticker")
        b = trunc[trunc["date"] == d].set_index("ticker")
        for side, have, lack in (("trunc", a, b), ("full", b, a)):
            gone = sorted(set(have.index) - set(lack.index))
            if gone:
                raise AssertionError(
                    f"lookahead check on {d.date()}: ticker {gone[0]} is missing from the {side} output")
        cols = [c for c in full.columns if c not in ("date", "ticker")]
        for tk in sorted(a.index):
            for c in cols:
                va, vb = a.at[tk, c], b.at[tk, c]
                if not _same(va, vb, atol):
                    raise AssertionError(
                        f"lookahead in column {c!r} on {d.date()} for {tk}: "
                        f"full-sample value {va!r} != truncated value {vb!r}")
