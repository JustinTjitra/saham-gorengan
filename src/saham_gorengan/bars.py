"""Canonical daily-bar panel: the one format every source converts into."""
from __future__ import annotations

import pandas as pd

BAR_COLUMNS: dict[str, str] = {
    "date": "datetime64[ns]",  # normalised to midnight, no timezone
    "ticker": "string",  # 4 uppercase letters
    "open": "float64",
    "high": "float64",
    "low": "float64",
    "close": "float64",
    "adj_close": "float64",  # NaN when the source has none
    "volume": "float64",  # shares; NaN = unknown, 0 = no trades
    "value": "float64",  # IDR
    "frequency": "Int64",  # number of trades
    "foreign_buy": "float64",
    "foreign_sell": "float64",
    "listed_shares": "float64",
    "tradeable_shares": "float64",
    "source": "string",
}
OPTIONAL = ["adj_close", "value", "frequency", "foreign_buy", "foreign_sell",
            "listed_shares", "tradeable_shares"]
REQUIRED = [c for c in BAR_COLUMNS if c not in OPTIONAL]
PRICES = ["open", "high", "low", "close"]
MAX_EXAMPLES = 5


class BarsValidationError(ValueError):
    """Raised when a bars frame does not meet the canonical schema."""


def empty_bars() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype=t) for c, t in BAR_COLUMNS.items()})


def _describe(df: pd.DataFrame, mask: pd.Series, label: str) -> str | None:
    n = int(mask.sum())
    if n == 0:
        return None
    rows = df.loc[mask, ["date", "ticker"]].head(MAX_EXAMPLES)
    ex = ", ".join(f"({d}, {t})" for d, t in zip(rows["date"], rows["ticker"]))
    return f"{label}: {n} row(s), e.g. {ex}"


def validate_bars(df: pd.DataFrame) -> pd.DataFrame:
    """Return a coerced copy of ``df`` in canonical form, or raise BarsValidationError."""
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise BarsValidationError(f"missing required columns: {missing}")
    extra = [c for c in df.columns if c not in BAR_COLUMNS]
    if extra:
        raise BarsValidationError(f"unexpected columns: {extra}")

    out = df.copy()
    for c in OPTIONAL:
        if c not in out.columns:
            out[c] = pd.NA
    out = out[list(BAR_COLUMNS)].reset_index(drop=True)

    problems: list[str] = []

    def coerce(col: str, fn) -> None:
        try:
            out[col] = fn(out[col])
        except (ValueError, TypeError, OverflowError) as exc:
            problems.append(f"cannot coerce column {col!r}: {exc}")

    tz_aware = False
    has_time = pd.Series(False, index=out.index)

    def to_date(s: pd.Series) -> pd.Series:
        nonlocal tz_aware, has_time
        d = pd.to_datetime(s)
        if getattr(d.dt, "tz", None) is not None:
            tz_aware = True
            d = d.dt.tz_localize(None)
        has_time = d.notna() & (d != d.dt.normalize())
        return d.astype("datetime64[ns]")

    coerce("date", to_date)
    coerce("ticker", lambda s: s.astype("string"))
    coerce("source", lambda s: s.astype("string"))
    for c, t in BAR_COLUMNS.items():
        if t == "float64":
            coerce(c, lambda s: pd.to_numeric(s).astype("float64"))
    coerce("frequency", lambda s: pd.to_numeric(s).astype("Int64"))
    if problems:  # row checks need clean dtypes
        raise BarsValidationError("; ".join(problems))
    # missing optional columns were pd.NA; make sure they ended up float/Int64
    out = out.astype(BAR_COLUMNS)

    def add(mask: pd.Series, label: str) -> None:
        msg = _describe(out, mask.fillna(False).astype(bool), label)
        if msg:
            problems.append(msg)

    if tz_aware:
        problems.append("dates carry a timezone (convert to naive local dates first)")
    add(has_time, "dates with a time component")
    add(out["date"].isna(), "missing date")
    add(out["source"].isna(), "missing source")
    add(out.duplicated(["date", "ticker"], keep=False), "duplicate (date, ticker)")
    add(~out["ticker"].str.fullmatch(r"[A-Z]{4}"), "ticker not matching ^[A-Z]{4}$")
    add(out[PRICES].isna().any(axis=1), "missing price (NaN open/high/low/close)")
    add((out[PRICES] <= 0).any(axis=1), "non-positive open/high/low/close")
    add(out["high"] < out[["open", "close", "low"]].max(axis=1), "high below max(open, close, low)")
    add(out["low"] > out[["open", "close", "high"]].min(axis=1), "low above min(open, close, high)")
    for c in ("volume", "value", "frequency"):
        add(out[c] < 0, f"negative {c}")

    if problems:
        raise BarsValidationError(f"{len(problems)} problem(s) in bars:\n" + "\n".join(problems))
    return out.sort_values(["date", "ticker"], kind="stable").reset_index(drop=True)
