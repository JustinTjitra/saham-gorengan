"""IDX ticker-universe file (ticker, listed, delisted, source) and per-ticker fetch plan."""
from __future__ import annotations

import csv
import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd

HEADER = ["ticker", "listed", "delisted", "source"]
_TICKER = re.compile(r"[A-Z]{4}")


def _parse_date(text: str, line: int, name: str) -> pd.Timestamp:
    try:
        return pd.Timestamp(datetime.strptime(text.strip(), "%Y-%m-%d"))
    except ValueError:
        raise ValueError(f"line {line}: bad {name} date {text!r}, expected YYYY-MM-DD") from None


def load_universe(path: str | Path) -> pd.DataFrame:
    """Columns ticker (string), listed (datetime64[ns]), delisted (datetime64[ns], NaT = still listed), source (string)."""
    rows: list[tuple] = []
    seen: set[str] = set()
    with open(path, newline="", encoding="utf-8-sig") as fh:  # tolerate the BOM Excel adds
        reader = csv.reader(fh)
        header = next(reader, None)
        if header != HEADER:
            raise ValueError(f"line 1: header must be {','.join(HEADER)}, got {header!r}")
        for fields in reader:
            line = reader.line_num
            if not fields:
                continue
            if len(fields) != len(HEADER):
                raise ValueError(f"line {line}: expected {len(HEADER)} fields, got {len(fields)}")
            ticker, listed_s, delisted_s, source = fields
            if not _TICKER.fullmatch(ticker):
                raise ValueError(f"line {line}: ticker {ticker!r} is not 4 uppercase letters A-Z")
            if ticker in seen:
                raise ValueError(f"line {line}: duplicate ticker {ticker}")
            seen.add(ticker)
            listed = _parse_date(listed_s, line, "listed")
            delisted = _parse_date(delisted_s, line, "delisted") if delisted_s.strip() else pd.NaT
            if delisted is not pd.NaT and delisted < listed:
                raise ValueError(f"line {line}: delisted {delisted_s} is before listed {listed_s}")
            if not source.strip():
                raise ValueError(f"line {line}: source must not be empty")
            rows.append((ticker, listed, delisted, source.strip()))
    df = pd.DataFrame(rows, columns=HEADER)
    df["ticker"] = df["ticker"].astype("string")
    df["source"] = df["source"].astype("string")
    df["listed"] = pd.to_datetime(df["listed"]).astype("datetime64[ns]")
    df["delisted"] = pd.to_datetime(df["delisted"]).astype("datetime64[ns]")
    return df


def active_on(universe: pd.DataFrame, day: date) -> list[str]:
    """Sorted tickers listed on or before `day` and not delisted before `day`."""
    d = pd.Timestamp(day)
    mask = (universe["listed"] <= d) & (universe["delisted"].isna() | (universe["delisted"] >= d))
    return sorted(str(t) for t in universe.loc[mask, "ticker"])


def fetch_plan(universe: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    """Columns ticker, start, end (datetime64[ns]): each ticker's listed period clipped to [start, end]."""
    if start > end:
        raise ValueError(f"start {start} is after end {end}")
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    out = pd.DataFrame(
        {
            "ticker": universe["ticker"].astype("string"),
            "start": universe["listed"].clip(lower=s),
            "end": universe["delisted"].fillna(e).clip(upper=e),
        }
    )
    out = out[out["start"] <= out["end"]].sort_values("ticker").reset_index(drop=True)
    for c in ("start", "end"):
        out[c] = out[c].astype("datetime64[ns]")
    return out
