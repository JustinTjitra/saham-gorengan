"""Alert burden and weak-label overlap of the top-k flags (PLAN.md 3.4). Weak numbers are never for tuning."""
from __future__ import annotations

import numpy as np
import pandas as pd

_RANKS_REQ = ("date", "ticker", "rank")
_WEAK_REQ = ("date", "ticker", "weak")


def _check_int(name: str, v: object, minimum: int) -> None:
    if isinstance(v, bool) or not isinstance(v, (int, np.integer)) or v < minimum:
        raise ValueError(f"{name} must be an int >= {minimum}, got {v!r}")


def _require(df: pd.DataFrame, cols: tuple[str, ...], label: str) -> None:
    for c in cols:
        if c not in df.columns:
            raise ValueError(f"{label}: missing required column: {c}")


def _ratio(num: float, den: float) -> float:
    return float(num / den) if den else float("nan")


def alert_stats(ranks: pd.DataFrame, k: int = 25, weak: pd.DataFrame | None = None) -> dict[str, float]:
    """ranks: date, ticker, rank (Int64). weak: date, ticker, weak ("boolean"), e.g. ara_episode from P3-02.
    Returns flags_per_day, distinct_tickers, flags_per_ticker, and when weak is given
    share_flags_weak and share_weak_flagged. All values are plain floats; distinct_tickers is a count
    returned as float so the dict is uniform.

    A flag is a row with rank <= k (NA is not a flag). Days are the unique dates in ranks. Rows missing
    from weak, or with NA weak, count as not weak. share_weak_flagged is over weak rows present in ranks."""
    _check_int("k", k, 1)
    _require(ranks, _RANKS_REQ, "ranks")
    r = pd.DataFrame({
        "date": pd.to_datetime(ranks["date"]).to_numpy(),
        "ticker": ranks["ticker"].astype(str).to_numpy(),
        "rank": ranks["rank"].astype("Int64").to_numpy(),
    })
    if r.duplicated(["date", "ticker"]).any():
        raise ValueError("ranks has duplicate (date, ticker) rows")
    r["flag"] = (r["rank"].notna() & (r["rank"].fillna(k + 1) <= k)).to_numpy()

    n_days = r["date"].nunique()
    n_flags = int(r["flag"].sum())
    distinct = int(r.loc[r["flag"], "ticker"].nunique())
    out = {
        "flags_per_day": _ratio(n_flags, n_days),
        "distinct_tickers": float(distinct),
        "flags_per_ticker": _ratio(n_flags, distinct),
    }

    if weak is not None:
        _require(weak, _WEAK_REQ, "weak")
        w = pd.DataFrame({
            "date": pd.to_datetime(weak["date"]).to_numpy(),
            "ticker": weak["ticker"].astype(str).to_numpy(),
            "weak": weak["weak"].astype("boolean").to_numpy(),
        })
        if w.duplicated(["date", "ticker"]).any():
            raise ValueError("weak has duplicate (date, ticker) rows")
        m = r.merge(w, on=["date", "ticker"], how="left")
        is_weak = m["weak"].fillna(False).astype(bool)
        weak_flags = int((is_weak & m["flag"]).sum())
        out["share_flags_weak"] = _ratio(weak_flags, n_flags)
        out["share_weak_flagged"] = _ratio(weak_flags, int(is_weak.sum()))
    return out
