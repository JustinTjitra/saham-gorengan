"""Markdown evaluation report: recall vs placebo and random, alert burden, per-case results (PLAN.md 3.4)."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Sequence

import pandas as pd

from saham_gorengan._query import price_limits
from saham_gorengan.evaluation.metrics import recall_at_k

NOTE = ("Placebo and random baselines are mandatory comparisons (PLAN.md 3.4); "
        "a detector is only useful where it clearly beats both.")
_NA = "n/a"
_STRATA_ORDER = ("ARB 7%", "other", "unknown")


@dataclass
class DetectorResult:
    name: str
    case_metrics: pd.DataFrame       # window_metrics output on the real labelled windows
    placebo_metrics: pd.DataFrame    # window_metrics output on placebo windows
    random_metrics: pd.DataFrame     # window_metrics on real windows using random_ranks
    burden: dict[str, float]         # alert_stats output


def _num(v: object) -> str:
    if v is None or v is pd.NA:
        return _NA
    f = float(v)
    return _NA if math.isnan(f) else f"{f:.2f}"


def _int(v: object) -> str:
    if v is None or v is pd.NA:
        return _NA
    f = float(v)
    return _NA if math.isnan(f) else str(int(round(f)))


def _median_offset(v: object) -> str:
    """Median of integer offsets: an integer, or one decimal when it falls halfway (e.g. -0.5)."""
    if v is None or v is pd.NA or math.isnan(float(v)):
        return _NA
    f = float(v)
    return str(int(f)) if f.is_integer() else f"{f:.1f}"


def _found_cases(m: pd.DataFrame) -> pd.DataFrame:
    return m[m["found"].fillna(False).astype(bool)]


def _check(results: Sequence[DetectorResult]) -> list[str]:
    if len(results) == 0:
        raise ValueError("results is empty")
    ref: list[str] | None = None
    for r in results:
        ids = [str(x) for x in r.case_metrics["window_id"]]
        if len(set(ids)) != len(ids):
            raise ValueError(f"{r.name}: duplicate window_id in case_metrics")
        if ref is None:
            ref = sorted(ids)
        elif sorted(ids) != ref:
            raise ValueError("detectors have different window_id sets")
    assert ref is not None
    return ref


def window_strata(windows: pd.DataFrame) -> dict[str, str]:
    """Map window_id -> "ARB 7%" | "other" | "unknown" from the price-limit regime at window start."""
    ids = [str(x) for x in windows["window_id"]]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate window_id in windows")
    out: dict[str, str] = {}
    for wid, start in zip(ids, windows["start"]):
        try:
            arb = price_limits(pd.Timestamp(start).date(), 1000.0, "regular").arb_pct
        except ValueError:
            out[wid] = "unknown"
            continue
        out[wid] = "ARB 7%" if arb == 7 else "other"
    return out


def _strata_section(results: Sequence[DetectorResult], window_ids: list[str],
                    strata: Mapping[str, str]) -> list[str]:
    missing = [w for w in window_ids if w not in strata]
    if missing:
        raise ValueError(f"strata missing window_ids: {missing}")
    present = [s for s in _STRATA_ORDER if any(strata[w] == s for w in window_ids)]
    head = ["detector"] + present
    out = ["## Recall by price-limit regime", "",
           "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in results:
        cm = r.case_metrics.assign(window_id=r.case_metrics["window_id"].astype(str))
        cells = [r.name]
        for st in present:
            sub = cm[cm["window_id"].map(lambda w: strata[w] == st)]
            n = int((sub["n_days"].fillna(0) > 0).sum())
            cells.append(f"{_num(recall_at_k(sub))} (n={n})")
        out.append("| " + " | ".join(cells) + " |")
    out.append("")
    return out


def render_report(results: Sequence[DetectorResult], k: int, lead: int, title: str = "Evaluation",
                  strata: Mapping[str, str] | None = None) -> str:
    window_ids = _check(results)
    out = [f"# {title}", "",
           f"Top-k with k={k}, lead={lead} trading days. Results are statistical anomaly detection "
           "on labelled cases, not findings.", ""]

    head = ["detector", "recall cases", "recall placebo", "recall random", "median share",
            "median offset", "flags/day", "distinct tickers"]
    out += ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in results:
        cm = r.case_metrics
        found = _found_cases(cm)
        cells = [
            r.name,
            _num(recall_at_k(cm)),
            _num(recall_at_k(r.placebo_metrics)),
            _num(recall_at_k(r.random_metrics)),
            _num(cm["share_in_topk"].astype("float64").median(skipna=True)),
            _median_offset(found["first_flag_offset"].astype("Int64").dropna().astype(float).median()),
            _num(r.burden.get("flags_per_day")),
            _int(r.burden.get("distinct_tickers")),
        ]
        out.append("| " + " | ".join(cells) + " |")
    out.append("")

    head2 = ["window_id", "ticker"]
    for r in results:
        head2 += [f"{r.name} found", f"{r.name} offset"]
    out += ["| " + " | ".join(head2) + " |", "|" + "---|" * len(head2)]
    indexed = [r.case_metrics.assign(window_id=r.case_metrics["window_id"].astype(str))
               .set_index("window_id") for r in results]
    for wid in window_ids:
        row = [wid, str(indexed[0].at[wid, "ticker"])]
        for m in indexed:
            f = m.at[wid, "found"]
            is_found = bool(f) if f is not pd.NA else False
            row += ["yes" if is_found else "no",
                    _int(m.at[wid, "first_flag_offset"]) if is_found else _NA]
        out.append("| " + " | ".join(row) + " |")
    out.append("")
    if strata is not None:
        out += _strata_section(results, window_ids, strata)
    out += [NOTE, ""]
    return "\n".join(out)
