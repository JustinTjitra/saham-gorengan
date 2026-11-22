from datetime import date

import pandas as pd
import pytest

from saham_gorengan._load import Window
from saham_gorengan.evaluation.metrics import window_metrics
from saham_gorengan.evaluation.pipeline import default_detectors, evaluate, windows_frame
from saham_gorengan.evaluation.report import render_report
from saham_gorengan.features.assemble import build_features
from saham_gorengan.testing import Pump, synthetic_bars

K, LEAD = 10, 5
PUMP_TICKER = "SYAC"


@pytest.fixture(scope="module")
def panel():
    days = pd.bdate_range("2024-01-02", "2024-12-31")
    s, e = days[120], days[134]
    bars = synthetic_bars(40, date(2024, 1, 2), date(2024, 12, 31), 0,
                          [Pump(ticker=PUMP_TICKER, start=s.date())])
    features = build_features(bars)
    windows = pd.DataFrame([{"window_id": "PUMP-1", "ticker": PUMP_TICKER, "start": s, "end": e}])
    return features, windows


@pytest.fixture(scope="module")
def dets(panel):
    return default_detectors(panel[0])


def _results(panel, dets, windows=None, **kw):
    kw.setdefault("n_placebo", 5)
    return evaluate(panel[0], panel[1] if windows is None else windows, dets, k=K, lead=LEAD, **kw)


def _w(wid, ticker, s, e):
    return Window(window_id=wid, case_id="C", ticker=ticker, start=s, end=e,
                  precision="day", label_class="x", confidence="high", notes="")


def test_windows_frame():
    f = windows_frame([_w("B", "AAAA", date(2024, 3, 4), date(2024, 3, 8)),
                       _w("A", "BBBB", date(2024, 5, 1), date(2024, 5, 3))])
    assert list(f.columns) == ["window_id", "ticker", "start", "end"]
    assert list(f["window_id"]) == ["B", "A"]
    assert str(f["ticker"].dtype) == "string"
    assert str(f["start"].dtype) == "datetime64[ns]" and str(f["end"].dtype) == "datetime64[ns]"
    assert f["start"].iloc[0] == pd.Timestamp("2024-03-04")


def test_default_detectors_keys(panel):
    d = default_detectors(panel[0])
    assert list(d) == ["rank_ret", "rank_vol", "rank_rule", "composite"]
    for v in d.values():
        assert list(v.columns) == ["date", "ticker", "rank"]
    d2 = default_detectors(panel[0], include_iforest=True)
    assert list(d2) == ["rank_ret", "rank_vol", "rank_rule", "composite", "iforest"]
    assert list(d2["iforest"].columns) == ["date", "ticker", "rank"]


def test_evaluate_shapes(panel, dets):
    res = _results(panel, dets)
    assert [r.name for r in res] == list(dets)
    for r in res:
        assert len(r.case_metrics) == 1
        assert len(r.placebo_metrics) == 5
        assert len(r.random_metrics) == 1
        assert {"flags_per_day", "distinct_tickers"} <= set(r.burden)


def test_case_metrics_match(panel, dets):
    for r in _results(panel, dets):
        pd.testing.assert_frame_equal(r.case_metrics, window_metrics(dets[r.name], panel[1], K, LEAD))


def test_strong_pump_found(panel, dets):
    comp = [r for r in _results(panel, dets) if r.name == "composite"][0]
    assert bool(comp.case_metrics["found"].iloc[0])


def test_unknown_ticker_dropped(panel, dets):
    extra = pd.concat([panel[1], pd.DataFrame([{"window_id": "X", "ticker": "NOPE",
                                                "start": pd.Timestamp("2024-06-03"),
                                                "end": pd.Timestamp("2024-06-14")}])],
                      ignore_index=True)
    a, b = _results(panel, dets), _results(panel, dets, windows=extra)
    for x, y in zip(a, b):
        pd.testing.assert_frame_equal(x.case_metrics, y.case_metrics)
        pd.testing.assert_frame_equal(x.placebo_metrics, y.placebo_metrics)
        pd.testing.assert_frame_equal(x.random_metrics, y.random_metrics)
        assert x.burden == y.burden


def test_deterministic(panel, dets):
    a, b = _results(panel, dets, seed=3), _results(panel, dets, seed=3)
    for x, y in zip(a, b):
        pd.testing.assert_frame_equal(x.placebo_metrics, y.placebo_metrics)
        pd.testing.assert_frame_equal(x.random_metrics, y.random_metrics)


def test_inputs_not_modified(panel, dets):
    f0, w0 = panel[0].copy(), panel[1].copy()
    d0 = {k: v.copy() for k, v in dets.items()}
    _results(panel, dets)
    pd.testing.assert_frame_equal(f0, panel[0])
    pd.testing.assert_frame_equal(w0, panel[1])
    for k, v in d0.items():
        pd.testing.assert_frame_equal(v, dets[k])


def test_render_roundtrip(panel, dets):
    assert PUMP_TICKER in render_report(_results(panel, dets), K, LEAD)


def test_bad_input(panel, dets):
    with pytest.raises(ValueError):
        evaluate(panel[0], panel[1], {})
    unknown = pd.DataFrame([{"window_id": "X", "ticker": "NOPE",
                             "start": pd.Timestamp("2024-06-03"), "end": pd.Timestamp("2024-06-14")}])
    with pytest.raises(ValueError):
        evaluate(panel[0], unknown, dets)
    with pytest.raises(ValueError):
        evaluate(panel[0].drop(columns="liq_bucket"), panel[1], dets)


def test_iforest_columns(panel):
    d = default_detectors(panel[0], include_iforest=True)
    res = evaluate(panel[0], panel[1], d, k=K, lead=LEAD, n_placebo=2)
    assert res[-1].name == "iforest"
