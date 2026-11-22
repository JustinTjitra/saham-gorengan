"""Watchlist writer: top-k composite scores with neutral explanations (PLAN.md 3.5)."""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .store import store_root

DISCLAIMER = ("Statistical anomaly ranking only; "
              "it does not state or imply that any party manipulated a stock.")
_FORBIDDEN = ("manipul", "goreng", "fraud", "pump", "scam")
COLUMNS = ["date", "ticker", "rank", "score", "drivers"]


def explain(features_row: pd.Series, composite_row: pd.Series, top_n: int = 3) -> str:
    """Neutral sentence listing the top_n z-components with the largest absolute value."""
    items = []
    for name, value in composite_row.items():
        if isinstance(name, str) and name.startswith("z_") and pd.notna(value):
            items.append((name[2:], float(value)))
    items.sort(key=lambda t: (-abs(t[1]), t[0]))
    if not items[:top_n]:
        return "no components available"
    return ", ".join(f"{n} {v:+.1f}" for n, v in items[:top_n])


def build_watchlist(day: date, features: pd.DataFrame, composite: pd.DataFrame,
                    k: int = 25) -> pd.DataFrame:
    """Columns date, ticker, rank (Int64), score (float64), drivers (string), sorted by rank."""
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError(f"k must be an int >= 1, got {k!r}")
    ts = pd.Timestamp(day)
    comp = composite[pd.to_datetime(composite["date"]) == ts]
    if comp.empty:
        raise ValueError(f"no scores for {day}")
    top = comp[comp["rank"].notna() & (comp["rank"] <= k)].sort_values("rank", kind="mergesort")

    feats = features[pd.to_datetime(features["date"]) == ts].set_index("ticker")
    empty = pd.Series(dtype="float64")
    drivers = []
    for _, row in top.iterrows():
        frow = feats.loc[row["ticker"]] if row["ticker"] in feats.index else empty
        if isinstance(frow, pd.DataFrame):
            frow = frow.iloc[0]
        drivers.append(explain(frow, row))
    for text in drivers:
        low = text.lower()
        if any(w in low for w in _FORBIDDEN):
            raise ValueError(f"drivers text breaks the wording rules: {text!r}")

    return pd.DataFrame({
        "date": pd.to_datetime(top["date"]).astype("datetime64[ns]").to_numpy(),
        "ticker": top["ticker"].astype("string").to_numpy(),
        "rank": pd.array(top["rank"].to_numpy(), dtype="Int64"),
        "score": top["score"].astype("float64").to_numpy(),
        "drivers": pd.array(drivers, dtype="string"),
    }, columns=COLUMNS)


def write_watchlist(df: pd.DataFrame, root: str | Path | None = None) -> Path:
    """Write <root>/watchlist/YYYY/YYYY-MM-DD.parquet atomically; return the path."""
    base = store_root(root)
    days = pd.to_datetime(df["date"]).dt.normalize().unique()
    if len(days) != 1:
        raise ValueError("watchlist must hold exactly one date")
    day = pd.Timestamp(days[0])
    path = base / "watchlist" / f"{day.year:04d}" / f"{day.date().isoformat()}.parquet"
    table = pa.Table.from_pandas(df, preserve_index=False)
    meta = dict(table.schema.metadata or {})
    meta[b"disclaimer"] = DISCLAIMER.encode()
    table = table.replace_schema_metadata(meta)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    try:
        pq.write_table(table, tmp, compression="zstd")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)
    return path
