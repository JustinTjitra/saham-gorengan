"""Resumable month-by-month backfill from a DailySource into the private store."""
from __future__ import annotations

import calendar
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, Sequence

import pandas as pd

from .bars import BarsValidationError
from .sources.base import DailySource, SourceError
from .store import store_root, write_bars

log = logging.getLogger(__name__)


@dataclass
class BackfillReport:
    months_done: list[str] = field(default_factory=list)
    months_skipped: list[str] = field(default_factory=list)
    rows_written: int = 0
    failed: list[tuple[str, str, str]] = field(default_factory=list)


def _months(start: date, end: date) -> list[tuple[str, date, date]]:
    out = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        first, last = date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])
        out.append((f"{y:04d}-{m:02d}", max(first, start), min(last, end)))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def _read_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        state = json.loads(path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"corrupt backfill state file {path}: {exc}") from exc
    if not isinstance(state, dict):
        raise ValueError(f"corrupt backfill state file {path}: expected a JSON object")
    return state


def _write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    try:
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True))
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def backfill(source: DailySource, tickers: Sequence[str], start: date, end: date,
             root: str | Path | None = None, batch_size: int = 50, pause: float = 1.0,
             sleep: Callable[[float], None] = time.sleep) -> BackfillReport:
    if start > end:
        raise ValueError(f"start {start} is after end {end}")
    tks = sorted({t.strip().upper() for t in tickers if t and t.strip()})
    if not tks:
        raise ValueError("tickers is empty")
    if batch_size < 1:
        raise ValueError(f"batch_size must be >= 1, got {batch_size}")
    base = store_root(root)
    state_path = base / "state" / "backfill.json"
    state = _read_state(state_path)
    digest = hashlib.sha1("\n".join(tks).encode()).hexdigest()
    entry = state.get(source.name)
    if not isinstance(entry, dict) or entry.get("tickers_sha1") != digest:
        entry = {"tickers_sha1": digest, "complete": []}
    state[source.name] = entry

    report = BackfillReport()
    first_call = True

    def call(batch: list[str], s: date, e: date) -> pd.DataFrame:
        nonlocal first_call
        if not first_call:
            sleep(pause)
        first_call = False
        return source.fetch(batch, s, e)

    for key, s, e in _months(start, end):
        if key in entry["complete"]:
            report.months_skipped.append(key)
            log.info("skip %s (complete)", key)
            continue
        frames = []
        for i in range(0, len(tks), batch_size):
            batch = tks[i:i + batch_size]
            try:
                frames.append(call(batch, s, e))
                continue
            except (BarsValidationError, SourceError) as exc:
                log.warning("%s batch of %d failed (%s); retrying per ticker", key, len(batch), exc)
            for tk in batch:
                try:
                    frames.append(call([tk], s, e))
                except (BarsValidationError, SourceError) as exc:
                    log.warning("%s %s failed: %s", key, tk, exc)
                    report.failed.append((key, tk, str(exc)))
        frames = [f for f in frames if len(f)]
        if frames:
            df = pd.concat(frames, ignore_index=True)
            write_bars(df, base)
            report.rows_written += len(df)
        entry["complete"] = sorted(set(entry["complete"]) | {key})
        _write_state(state_path, state)
        report.months_done.append(key)
        log.info("done %s", key)
    return report
