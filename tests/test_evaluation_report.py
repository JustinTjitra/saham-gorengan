import pandas as pd
import pytest

from saham_gorengan.evaluation.report import DetectorResult, render_report, window_strata


def _m(rows):
    return pd.DataFrame({
        "window_id": pd.array([r[0] for r in rows], dtype="string"),
        "ticker": pd.array([r[1] for r in rows], dtype="string"),
        "n_days": pd.array([r[2] for r in rows], dtype="Int64"),
        "found": pd.array([r[3] for r in rows], dtype="boolean"),
        "share_in_topk": pd.array([r[4] for r in rows], dtype="float64"),
        "first_flag_offset": pd.array([r[5] for r in rows], dtype="Int64"),
    })


def _a():
    cases = _m([("W3", "CCCC", 5, False, 0.0, pd.NA),
                ("W1", "AAAA", 5, True, 0.5, -3),
                ("W2", "BBBB", 5, True, 1.0, 2)])
    placebo = _m([("P1", "PLAC", 5, True, 0.2, 1),
                  ("P2", "PLBD", 5, False, 0.0, pd.NA)])
    rnd = _m([("W1", "AAAA", 5, False, 0.0, pd.NA),
              ("W2", "BBBB", 5, False, 0.0, pd.NA),
              ("W3", "CCCC", 5, False, 0.0, pd.NA)])
    return DetectorResult("A", cases, placebo, rnd,
                          {"flags_per_day": 3.5, "distinct_tickers": 12.0})


def _b():
    cases = _m([("W1", "AAAA", 5, False, 0.0, pd.NA),
                ("W2", "BBBB", 5, True, 0.25, 4),
                ("W3", "CCCC", 5, False, 0.0, pd.NA)])
    placebo = _m([("P1", "PLAC", 0, False, float("nan"), pd.NA)])
    rnd = _m([("W1", "AAAA", 5, False, 0.0, pd.NA)])
    return DetectorResult("B", cases, placebo, rnd, {"flags_per_day": 1.0})


def _rows(text):
    return [ln for ln in text.splitlines() if ln.startswith("|")]


def test_summary_numbers():
    out = render_report([_a(), _b()], k=25, lead=20)
    rows = _rows(out)
    assert rows[0] == ("| detector | recall cases | recall placebo | recall random | "
                       "median share | median offset | flags/day | distinct tickers |")
    a = [r for r in rows if r.startswith("| A |")][0]
    assert a == "| A | 0.67 | 0.50 | 0.00 | 0.50 | -0.5 | 3.50 | 12 |"
    b = [r for r in rows if r.startswith("| B |")][0]
    assert b == "| B | 0.33 | n/a | 0.00 | 0.00 | 4 | 1.00 | n/a |"


def test_summary_median_offset_na_when_none_found():
    a = _a()
    a.case_metrics["found"] = pd.array([False] * 3, dtype="boolean")
    a.case_metrics["first_flag_offset"] = pd.array([pd.NA] * 3, dtype="Int64")
    out = render_report([a], k=5, lead=1)
    row = [r for r in _rows(out) if r.startswith("| A |")][0]
    assert row.split("|")[6].strip() == "n/a"


def test_per_case_table():
    out = render_report([_a(), _b()], k=25, lead=20)
    rows = _rows(out)
    i = [n for n, r in enumerate(rows) if r.startswith("| window_id")][0]
    assert rows[i] == "| window_id | ticker | A found | A offset | B found | B offset |"
    body = rows[i + 2:]
    assert body == [
        "| W1 | AAAA | yes | -3 | no | n/a |",
        "| W2 | BBBB | yes | 2 | yes | 4 |",
        "| W3 | CCCC | no | n/a | no | n/a |",
    ]


def test_mandatory_note_present():
    out = render_report([_a()], k=25, lead=20)
    assert ("Placebo and random baselines are mandatory comparisons (PLAN.md 3.4); "
            "a detector is only useful where it clearly beats both.") in out


def test_title_and_params():
    out = render_report([_a()], k=25, lead=20, title="My Eval")
    lines = out.splitlines()
    assert lines[0] == "# My Eval"
    assert "k=25" in out and "lead=20" in out
    assert "statistical anomaly" in out and "not findings" in out
    assert "manipulat" not in out.lower()
    assert render_report([_a()], k=25, lead=20) == render_report([_a()], k=25, lead=20)


def test_no_foreign_tickers():
    out = render_report([_a(), _b()], k=25, lead=20)
    assert "PLAC" not in out and "PLBD" not in out and "P1" not in out


def test_bad_input():
    with pytest.raises(ValueError):
        render_report([], k=25, lead=20)
    b = _b()
    b.case_metrics = b.case_metrics.iloc[:2]
    with pytest.raises(ValueError):
        render_report([_a(), b], k=25, lead=20)
    dup = _a()
    dup.case_metrics = pd.concat([dup.case_metrics, dup.case_metrics.iloc[:1]])
    with pytest.raises(ValueError):
        render_report([dup], k=25, lead=20)


_NO_STRATA_EXPECTED = (
    "# Evaluation\n\nTop-k with k=25, lead=20 trading days. Results are statistical anomaly "
    "detection on labelled cases, not findings.\n\n"
    "| detector | recall cases | recall placebo | recall random | median share | median offset "
    "| flags/day | distinct tickers |\n"
    "|---|---|---|---|---|---|---|---|\n"
    "| A | 0.67 | 0.50 | 0.00 | 0.50 | -0.5 | 3.50 | 12 |\n"
    "| B | 0.33 | n/a | 0.00 | 0.00 | 4 | 1.00 | n/a |\n\n"
    "| window_id | ticker | A found | A offset | B found | B offset |\n"
    "|---|---|---|---|---|---|\n"
    "| W1 | AAAA | yes | -3 | no | n/a |\n"
    "| W2 | BBBB | yes | 2 | yes | 4 |\n"
    "| W3 | CCCC | no | n/a | no | n/a |\n\n"
    "Placebo and random baselines are mandatory comparisons (PLAN.md 3.4); "
    "a detector is only useful where it clearly beats both.\n"
)


def test_window_strata():
    w = pd.DataFrame({
        "window_id": ["X1", "X2", "X3"],
        "start": pd.to_datetime(["2021-06-01", "2024-06-03", "2000-01-03"]),
    })
    assert window_strata(w) == {"X1": "ARB 7%", "X2": "other", "X3": "unknown"}
    with pytest.raises(ValueError):
        window_strata(pd.concat([w, w.iloc[:1]]))


def test_strata_table():
    strata = {"W1": "ARB 7%", "W2": "ARB 7%", "W3": "other"}
    out = render_report([_a(), _b()], k=25, lead=20, strata=strata)
    rows = _rows(out)
    i = [n for n, r in enumerate(rows) if r.startswith("| detector | ARB")][0]
    assert rows[i] == "| detector | ARB 7% | other |"
    assert rows[i + 2] == "| A | 1.00 (n=2) | 0.00 (n=1) |"
    assert rows[i + 3] == "| B | 0.50 (n=2) | 0.00 (n=1) |"
    assert "## Recall by price-limit regime" in out
    assert out.index("| W3 |") < out.index("## Recall by price-limit regime") < out.index("Placebo and random")


def test_strata_n_zero_and_order():
    a = _a()
    a.case_metrics.loc[a.case_metrics["window_id"] == "W3", "n_days"] = 0
    strata = {"W1": "unknown", "W2": "ARB 7%", "W3": "other"}
    out = render_report([a], k=25, lead=20, strata=strata)
    rows = _rows(out)
    i = [n for n, r in enumerate(rows) if r.startswith("| detector | ARB")][0]
    assert rows[i] == "| detector | ARB 7% | other | unknown |"
    assert rows[i + 2] == "| A | 1.00 (n=1) | n/a (n=0) | 1.00 (n=1) |"


def test_no_strata_unchanged():
    assert render_report([_a(), _b()], k=25, lead=20) == _NO_STRATA_EXPECTED


def test_strata_missing_window():
    with pytest.raises(ValueError):
        render_report([_a(), _b()], k=25, lead=20, strata={"W1": "ARB 7%", "W2": "ARB 7%"})
