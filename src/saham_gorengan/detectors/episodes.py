"""Gap-based merging of flagged days into per-ticker episodes (PLAN.md 3.3, step 5)."""
from __future__ import annotations

import numpy as np
import pandas as pd

_REQUIRED = ("date", "ticker", "rank")


def _check_int(name: str, v: object, minimum: int) -> None:
    if isinstance(v, bool) or not isinstance(v, (int, np.integer)) or v < minimum:
        raise ValueError(f"{name} must be an int >= {minimum}, got {v!r}")


def _empty() -> pd.DataFrame:
    return pd.DataFrame({
        "episode_id": pd.Series([], dtype="string"),
        "ticker": pd.Series([], dtype="string"),
        "start": pd.Series([], dtype="datetime64[ns]"),
        "end": pd.Series([], dtype="datetime64[ns]"),
        "n_flag_days": pd.Series([], dtype="Int64"),
        "best_rank": pd.Series([], dtype="Int64"),
    })


def build_episodes(ranks: pd.DataFrame, k: int = 25, max_gap: int = 3,
                   min_flags: int = 1) -> pd.DataFrame:
    """ranks: date, ticker, rank (Int64; NA = unranked). Output, one row per episode:
    episode_id (string), ticker (string), start, end (datetime64[ns]), n_flag_days (Int64), best_rank (Int64).

    Trading days are the sorted unique ranks dates; a row is flagged when rank <= k (NA is not flagged).
    A new episode starts when more than `max_gap` trading days lie strictly between consecutive flagged
    days of a ticker. Episodes with fewer than `min_flags` flagged days are dropped. Sorted by
    (start, ticker). An episode's end uses later days: for reporting, not for scoring day D."""
    _check_int("k", k, 1)
    _check_int("max_gap", max_gap, 0)
    _check_int("min_flags", min_flags, 1)
    for c in _REQUIRED:
        if c not in ranks.columns:
            raise ValueError(f"missing required column: {c}")

    r = pd.DataFrame({
        "date": pd.to_datetime(ranks["date"]).astype("datetime64[ns]").to_numpy(),
        "ticker": ranks["ticker"].astype(str).to_numpy(),
        "rank": ranks["rank"].astype("Int64").to_numpy(),
    })
    if r.duplicated(["date", "ticker"]).any():
        raise ValueError("ranks has duplicate (date, ticker) rows")

    days = np.sort(r["date"].unique())
    flagged = r[(r["rank"] <= k).fillna(False).to_numpy(dtype=bool)].copy()
    if flagged.empty:
        return _empty()
    flagged["idx"] = np.searchsorted(days, flagged["date"].to_numpy())
    flagged = flagged.sort_values(["ticker", "idx"], kind="mergesort")

    rows = []
    for t, g in flagged.groupby("ticker", sort=True):
        idx = g["idx"].to_numpy()
        dates = g["date"].to_numpy()
        rk = g["rank"].to_numpy(dtype="int64")
        new = np.concatenate(([True], (idx[1:] - idx[:-1] - 1) > max_gap))
        ep = np.cumsum(new) - 1
        for e in range(int(ep[-1]) + 1):
            m = ep == e
            n = int(m.sum())
            if n < min_flags:
                continue
            rows.append((t, dates[m][0], dates[m][-1], n, int(rk[m].min())))
    if not rows:
        return _empty()

    out = pd.DataFrame(rows, columns=["ticker", "start", "end", "n_flag_days", "best_rank"])
    out = out.sort_values(["start", "ticker"], kind="mergesort").reset_index(drop=True)
    out["episode_id"] = out["ticker"] + "-" + out["start"].dt.strftime("%Y%m%d")
    out = out[["episode_id", "ticker", "start", "end", "n_flag_days", "best_rank"]]
    return out.astype({"episode_id": "string", "ticker": "string",
                       "start": "datetime64[ns]", "end": "datetime64[ns]",
                       "n_flag_days": "Int64", "best_rank": "Int64"})
