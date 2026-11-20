"""Corporate-action suspect flags for daily bars.

Flags days that are probably splits, reverse splits, rights or bonus issues
rather than trading, so later steps can exclude them instead of silently
adjusting prices (PLAN.md 3.1).

WARNING: rule 2 uses Yahoo's adjusted close, which Yahoo computes after the
fact (it embeds knowledge of later corporate actions). That is acceptable for
data cleaning, but this flag must NEVER be used as a model feature.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .bars import validate_bars
from .quality import quality_flags


def _near_whole(x: pd.Series, tol: float) -> pd.Series:
    """True where x is within ``tol`` (relative) of a whole number k >= 2."""
    k = np.round(x)
    with np.errstate(divide="ignore", invalid="ignore"):
        ok = (k >= 2) & ((x - k).abs() / k <= tol)
    return ok.fillna(False).astype(bool)


def corporate_action_suspects(bars: pd.DataFrame, board: str = "regular",
                              adj_jump: float = 0.05, ratio_tol: float = 0.03) -> pd.DataFrame:
    """Columns: date, ticker, suspect ("boolean"), price_ratio (float64, prev_close / close), kind (string).

    Same rows and order as ``validate_bars(bars)``; the input is not modified.

    Rule 1: ``quality_flags(bars, board)["beyond_limit"]`` is True.
    Rule 2: with ``f = adj_close / close``, ``abs(f / f_prev - 1) > adj_jump``;
    NA when adj_close is missing on either day or there is no previous bar.

    ``suspect``: True if any rule is True; False if no rule is True and at least
    one rule is evaluable (not NA); NA if both rules are NA.

    ``kind`` (only on suspect rows, NA elsewhere): "split" if price_ratio is within
    ``ratio_tol`` (relative) of a whole number k >= 2; "reverse_split" if
    1 / price_ratio is; otherwise "unknown".

    Only for data cleaning; never a model feature (rule 2 uses after-the-fact adjusted closes).
    """
    df = validate_bars(bars)
    rule1 = quality_flags(bars, board)["beyond_limit"].astype("boolean")

    g = df.groupby("ticker", sort=False)
    prev_close = g["close"].shift(1)
    f = df["adj_close"] / df["close"]
    f_prev = f.groupby(df["ticker"], sort=False).shift(1)
    jump = (f / f_prev - 1).abs() > adj_jump
    rule2 = jump.astype("boolean").mask(f.isna() | f_prev.isna(), pd.NA)

    any_true = rule1.fillna(False) | rule2.fillna(False)
    evaluable = rule1.notna() | rule2.notna()
    suspect = any_true.where(evaluable, pd.NA).astype("boolean")

    ratio = (prev_close / df["close"]).astype("float64")
    kind = pd.Series(np.where(_near_whole(ratio, ratio_tol), "split",
                              np.where(_near_whole(1 / ratio, ratio_tol), "reverse_split", "unknown")),
                     index=df.index, dtype="string")
    kind = kind.where(suspect.fillna(False).astype(bool), pd.NA).astype("string")

    out = df[["date", "ticker"]].copy()
    out["suspect"] = suspect
    out["price_ratio"] = ratio
    out["kind"] = kind
    return out.reset_index(drop=True)
