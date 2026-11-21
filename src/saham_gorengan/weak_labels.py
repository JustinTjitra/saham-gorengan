"""Weak labels for evaluation (PLAN.md 3.4): runs of consecutive ARA closes.

This is a LABEL, not a feature: an episode is defined by the whole run, including
days after D. It must never be a detector input or used in any score for day D.
An ARA run is a statistical price extreme, not a finding of manipulation.
Weak-label results are reported separately from the OJK labels and never tuned on.
"""
from __future__ import annotations

import pandas as pd

from .bars import validate_bars
from .features.limits import limit_features


def ara_run_label(bars: pd.DataFrame, min_run: int = 3, board: str = "regular") -> pd.DataFrame:
    """Columns: date, ticker, ara_episode ("boolean", never NA), episode_id (string), run_len (Int64).

    An episode is a maximal run of consecutive rows (per ticker, in date order) with
    ara_hit True and length >= ``min_run``; NA ara_hit counts as False and breaks a run.
    Same rows and order as ``validate_bars(bars)``.
    """
    if isinstance(min_run, bool) or not isinstance(min_run, int) or min_run < 1:
        raise ValueError(f"min_run must be an int >= 1, got {min_run!r}")
    df = validate_bars(bars)
    hit = limit_features(bars, board)["ara_hit"].fillna(False).to_numpy(dtype=bool)
    n = len(df)
    episode = [False] * n
    eid: list = [pd.NA] * n
    run_len: list = [pd.NA] * n

    rows_by_ticker: dict[str, list[int]] = {}
    for i, tk in enumerate(df["ticker"]):
        rows_by_ticker.setdefault(tk, []).append(i)  # df is date-sorted, so already in date order

    for tk, idx in rows_by_ticker.items():
        k = 0
        while k < len(idx):
            if not hit[idx[k]]:
                k += 1
                continue
            end = k
            while end + 1 < len(idx) and hit[idx[end + 1]]:
                end += 1
            length = end - k + 1
            if length >= min_run:
                start = df["date"].iloc[idx[k]]
                for j in idx[k:end + 1]:
                    episode[j] = True
                    eid[j] = f"{tk}-{start:%Y%m%d}"
                    run_len[j] = length
            k = end + 1

    return pd.DataFrame({
        "date": df["date"],
        "ticker": df["ticker"],
        "ara_episode": pd.Series(episode, dtype="boolean"),
        "episode_id": pd.Series(eid, dtype="string"),
        "run_len": pd.Series(run_len, dtype="Int64"),
    }).reset_index(drop=True)
