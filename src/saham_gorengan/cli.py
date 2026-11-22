"""Command line entry point: score one trading day from the local Parquet store."""
from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from .detectors.composite import composite_scores
from .features.assemble import build_features
from .store import read_bars

COLUMNS = ["date", "ticker", "rank", "score"]


def score_day(day: date, root: str | Path | None = None, k: int = 25,
              history_days: int = 400) -> pd.DataFrame:
    """Top-k composite ranks for `day`: columns date, ticker, rank (Int64), score (float64)."""
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError(f"k must be an int >= 1, got {k!r}")
    if isinstance(history_days, bool) or not isinstance(history_days, int) or history_days < 30:
        raise ValueError(f"history_days must be an int >= 30, got {history_days!r}")
    bars = read_bars(day - timedelta(days=history_days), day, root=root)
    ts = pd.Timestamp(day)
    if bars.empty or not (bars["date"] == ts).any():
        raise ValueError(f"no bars for {day}")
    scores = composite_scores(build_features(bars))
    out = scores[(scores["date"] == ts) & (scores["rank"] <= k)]
    out = out.sort_values("rank", kind="mergesort")
    return out[COLUMNS].reset_index(drop=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="saham-gorengan")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("score", help="print the top-k composite ranks for one trading day")
    p.add_argument("--date", required=True, help="trading day, YYYY-MM-DD")
    p.add_argument("--data-dir", default=None, help="data store root (default: $SAHAM_DATA_DIR)")
    p.add_argument("--k", type=int, default=25, help="number of rows to print (default 25)")
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return int(e.code) if isinstance(e.code, int) else 2
    if args.command != "score":
        parser.print_usage()
        return 2
    try:
        day = date.fromisoformat(args.date)
        out = score_day(day, root=args.data_dir, k=args.k)
    except (ValueError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    out = out.assign(date=out["date"].dt.strftime("%Y-%m-%d"))
    out.to_csv(sys.stdout, index=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
