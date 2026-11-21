"""Event-level recall, share-in-top-k and lead-time metrics per labelled window (PLAN.md 3.4)."""
from __future__ import annotations

import numpy as np
import pandas as pd

_RANKS_REQ = ("date", "ticker", "rank")
_WIN_REQ = ("window_id", "ticker", "start", "end")


def _check_int(name: str, v: object, minimum: int) -> None:
    if isinstance(v, bool) or not isinstance(v, (int, np.integer)) or v < minimum:
        raise ValueError(f"{name} must be an int >= {minimum}, got {v!r}")


def window_metrics(ranks: pd.DataFrame, windows: pd.DataFrame, k: int = 25,
                   lead: int = 20) -> pd.DataFrame:
    """ranks: columns date, ticker, rank (Int64; NA = unranked). windows: columns window_id, ticker, start, end.
    Output, one row per window (in windows order): window_id, ticker, n_days (Int64), found ("boolean"),
    share_in_topk (float64), first_flag_offset (Int64).

    Trading days T are the sorted unique ranks dates. Window days are T in [start, end]; the search span is
    the `lead` trading days before start plus the window days. If no trading day falls in the window,
    n_days is 0, share is NaN and found is evaluated over the lead days only.
    first_flag_offset is the index in T of the first flagged day in the span minus the index of the first
    trading day >= start. An NA rank is never in the top k."""
    _check_int("k", k, 1)
    _check_int("lead", lead, 0)
    for c in _RANKS_REQ:
        if c not in ranks.columns:
            raise ValueError(f"missing required column: {c}")
    for c in _WIN_REQ:
        if c not in windows.columns:
            raise ValueError(f"missing required column: {c}")

    r = pd.DataFrame({
        "date": pd.to_datetime(ranks["date"]).to_numpy(),
        "ticker": ranks["ticker"].astype(str).to_numpy(),
        "rank": ranks["rank"].astype("Int64").to_numpy(),
    })
    if r.duplicated(["date", "ticker"]).any():
        raise ValueError("ranks has duplicate (date, ticker) rows")
    days = np.sort(r["date"].unique())
    day_idx = {d: i for i, d in enumerate(days)}
    by_ticker = {t: g for t, g in r.groupby("ticker")}

    wid = windows["window_id"].astype(str).to_numpy()
    tick = windows["ticker"].astype(str).to_numpy()
    starts = pd.to_datetime(windows["start"]).to_numpy()
    ends = pd.to_datetime(windows["end"]).to_numpy()

    out = []
    for w, t, s, e in zip(wid, tick, starts, ends):
        i0 = int(np.searchsorted(days, s, side="left"))
        i_end = int(np.searchsorted(days, e, side="right"))  # exclusive
        lo = max(0, i0 - lead)
        hi = max(i_end, i0)
        n_days, found, share, off = 0, False, np.nan, pd.NA
        g = by_ticker.get(t)
        if g is not None:
            idx = np.array([day_idx[d] for d in g["date"]], dtype=int)
            flag = (g["rank"].notna() & (g["rank"].fillna(k + 1) <= k)).to_numpy()
            in_win = (idx >= i0) & (idx < i_end)
            n_days = int(in_win.sum())
            if n_days:
                share = float((flag & in_win).sum() / n_days)
            hits = idx[flag & (idx >= lo) & (idx < hi)]
            if hits.size:
                found = True
                off = int(hits.min()) - i0
        out.append((w, t, n_days, found, share, off))

    res = pd.DataFrame(out, columns=["window_id", "ticker", "n_days", "found",
                                     "share_in_topk", "first_flag_offset"])
    return pd.DataFrame({
        "window_id": res["window_id"].astype("string"),
        "ticker": res["ticker"].astype("string"),
        "n_days": res["n_days"].astype("Int64"),
        "found": res["found"].astype("boolean"),
        "share_in_topk": res["share_in_topk"].astype("float64"),
        "first_flag_offset": pd.array(res["first_flag_offset"].tolist(), dtype="Int64"),
    }).reset_index(drop=True)


def recall_at_k(metrics: pd.DataFrame) -> float:
    """Share of windows with found True, over windows with n_days > 0. NaN if there are none."""
    m = metrics[metrics["n_days"].fillna(0) > 0]
    if len(m) == 0:
        return float("nan")
    return float(m["found"].astype(bool).mean())
