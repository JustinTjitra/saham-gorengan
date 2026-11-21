"""Placebo windows and a random-ranker baseline for chance-level recall (PLAN.md 3.4)."""
from __future__ import annotations

import numpy as np
import pandas as pd

_MAX_DRAWS = 1000


def placebo_windows(windows: pd.DataFrame, panel: pd.DataFrame, n_per_window: int = 20,
                    seed: int = 0) -> pd.DataFrame:
    """windows: window_id, ticker, start, end. panel: date, ticker, liq_bucket.
    Output: window_id (f"{orig}-P{i:02d}"), orig_window_id, ticker, start, end (one row per placebo).

    Each placebo has the same trading-day length as its real window, a random other ticker in the
    same liquidity bucket (asof the placebo start) and no overlap with a real window of that ticker."""
    for c in ("window_id", "ticker", "start", "end"):
        if c not in windows.columns:
            raise ValueError(f"missing required column: {c}")
    for c in ("date", "ticker", "liq_bucket"):
        if c not in panel.columns:
            raise ValueError(f"missing required column: {c}")

    rng = np.random.default_rng(seed)
    p = pd.DataFrame({
        "date": pd.to_datetime(panel["date"]).to_numpy(),
        "ticker": panel["ticker"].astype(str).to_numpy(),
        "b": panel["liq_bucket"].astype("float64").to_numpy(),
    })
    days = np.sort(p["date"].unique())
    n_days = len(days)
    # (date x ticker) bucket view, forward-filled so row d holds the last non-NA bucket on dates <= d.
    raw = p.pivot_table(index="date", columns="ticker", values="b", aggfunc="last").reindex(days)
    grid = raw.ffill()
    tickers = np.array(grid.columns, dtype=object)
    bmat = grid.to_numpy(dtype="float64")  # asof view: the real ticker's last known bucket
    cmat = raw.to_numpy(dtype="float64")   # candidates must have a bucket ON the placebo start date
    col = {t: j for j, t in enumerate(tickers)}

    wid = windows["window_id"].astype(str).to_numpy()
    wt = windows["ticker"].astype(str).to_numpy()
    ws = pd.to_datetime(windows["start"]).to_numpy()
    we = pd.to_datetime(windows["end"]).to_numpy()
    real: dict[str, list[tuple]] = {}
    for t, s, e in zip(wt, ws, we):
        real.setdefault(t, []).append((s, e))

    out = []
    for w, t, s, e in zip(wid, wt, ws, we):
        i0 = int(np.searchsorted(days, s, side="left"))
        i1 = int(np.searchsorted(days, e, side="right"))
        length = i1 - i0
        if length <= 0:
            continue
        bucket = None  # "any"
        j = col.get(t)
        pos = int(np.searchsorted(days, s, side="right")) - 1
        if j is not None and pos >= 0 and not np.isnan(bmat[pos, j]):
            bucket = bmat[pos, j]
        if length > n_days:
            raise RuntimeError(f"no placebo span fits for window {w}")
        for i in range(n_per_window):
            for _ in range(_MAX_DRAWS):
                si = int(rng.integers(0, n_days - length + 1))
                if bucket is None:
                    ok = ~np.isnan(cmat[si])
                else:
                    ok = cmat[si] == bucket
                ok = ok & (tickers != t)
                cand = np.flatnonzero(ok)
                if cand.size == 0:
                    continue
                pt = tickers[int(cand[rng.integers(0, cand.size)])]
                ps, pe = days[si], days[si + length - 1]
                if any(ps <= re_ and pe >= rs for rs, re_ in real.get(pt, ())):
                    continue
                out.append((f"{w}-P{i:02d}", w, pt, ps, pe))
                break
            else:
                raise RuntimeError(f"no valid placebo found for window {w} after {_MAX_DRAWS} draws")

    res = pd.DataFrame(out, columns=["window_id", "orig_window_id", "ticker", "start", "end"])
    return pd.DataFrame({
        "window_id": res["window_id"].astype("string"),
        "orig_window_id": res["orig_window_id"].astype("string"),
        "ticker": res["ticker"].astype("string"),
        "start": pd.to_datetime(res["start"]).astype("datetime64[ns]"),
        "end": pd.to_datetime(res["end"]).astype("datetime64[ns]"),
    }).reset_index(drop=True)


def random_ranks(ranks: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """Same rows as `ranks` (date, ticker, rank); on each date the non-NA ranks are randomly permuted."""
    for c in ("date", "ticker", "rank"):
        if c not in ranks.columns:
            raise ValueError(f"missing required column: {c}")
    rng = np.random.default_rng(seed)
    out = ranks.reset_index(drop=True).copy()
    rk = out["rank"].astype("Int64")
    vals = rk.to_numpy(dtype="float64", na_value=np.nan)
    dates = pd.to_datetime(out["date"]).to_numpy()
    order = np.argsort(dates, kind="stable")
    sorted_dates = dates[order]
    bounds = np.flatnonzero(np.r_[True, sorted_dates[1:] != sorted_dates[:-1], True])
    new = vals.copy()
    for a, b in zip(bounds[:-1], bounds[1:]):
        idx = order[a:b]
        idx = idx[~np.isnan(vals[idx])]
        if idx.size:
            new[idx] = rng.permutation(vals[idx])
    out["rank"] = pd.array(np.where(np.isnan(new), pd.NA, new), dtype="Float64").astype("Int64")
    return out
