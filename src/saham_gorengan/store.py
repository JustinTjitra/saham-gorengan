"""Month-partitioned Parquet store for the daily bar panel (private, outside the repo)."""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Iterable

import pandas as pd

from .bars import empty_bars, validate_bars

ENV_VAR = "SAHAM_DATA_DIR"


def _repo_root() -> Path | None:
    for p in Path(__file__).resolve().parents:
        if (p / ".git").exists():
            return p
    return None


def store_root(root: str | Path | None = None) -> Path:
    raw = root if root is not None else os.environ.get(ENV_VAR)
    if not raw:
        raise RuntimeError(f"no data store: pass root or set {ENV_VAR}")
    path = Path(raw).expanduser().resolve()
    repo = _repo_root()
    if repo is not None and path.is_relative_to(repo):
        allowed = repo / "store"
        if not path.is_relative_to(allowed):
            raise RuntimeError(f"data store {path} is inside the git repo {repo}; "
                               f"use a directory outside it (or {allowed})")
    return path


def _month_file(root: Path, year: int, month: int) -> Path:
    return root / "bars" / f"year={year:04d}" / f"month={month:02d}" / "bars.parquet"


def write_bars(df: pd.DataFrame, root: str | Path | None = None) -> list[Path]:
    base = store_root(root)
    df = validate_bars(df)
    if df.empty:
        return []
    written: list[Path] = []
    for (year, month), part in df.groupby([df["date"].dt.year, df["date"].dt.month], sort=True):
        path = _month_file(base, int(year), int(month))
        if path.exists():
            old = pd.read_parquet(path, engine="pyarrow")
            part = pd.concat([old, part], ignore_index=True)
            part = part.drop_duplicates(["date", "ticker"], keep="last")
        part = validate_bars(part)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}")
        try:
            part.to_parquet(tmp, engine="pyarrow", compression="zstd", index=False)
            os.replace(tmp, path)
        finally:
            tmp.unlink(missing_ok=True)
        written.append(path)
    return written


def read_bars(start: date, end: date, tickers: Iterable[str] | None = None,
              root: str | Path | None = None) -> pd.DataFrame:
    if start > end:
        raise ValueError(f"start {start} is after end {end}")
    base = store_root(root)
    if not (base / "bars").is_dir():
        return empty_bars()
    frames = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        path = _month_file(base, y, m)
        if path.exists():
            frames.append(pd.read_parquet(path, engine="pyarrow"))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    if not frames:
        return empty_bars()
    df = pd.concat(frames, ignore_index=True)
    mask = (df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))
    if tickers is not None:
        mask &= df["ticker"].isin(list(tickers))
    return validate_bars(df[mask])
