"""Tests for the ticker-day label panel (P3-01)."""
from __future__ import annotations

import pandas as pd
import pytest

from saham_gorengan.labels import label_panel


def bars(*rows: tuple[str, str]) -> pd.DataFrame:
    return pd.DataFrame({
        "date": [pd.Timestamp(d) for d, _ in rows],
        "ticker": [t for _, t in rows],
        "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0,
        "volume": 1000.0, "source": "test",
    })


def one(day: str, ticker: str, **kw) -> pd.Series:
    return label_panel(bars((day, ticker)), **kw).iloc[0]


def test_convicted_in_default():
    r = one("2018-06-20", "SWAT")
    assert r["label"] and r["n_windows"] == 1
    assert (r["label_class"], r["confidence"], r["window_id"]) == ("convicted", "B", "SWAT-2018-1")


def test_alleged_off_by_default():
    assert not one("2021-06-01", "BEBS")["label"]
    assert one("2021-06-01", "BEBS", classes={"alleged"})["label"]


def test_bounds_inclusive():
    out = label_panel(bars(("2018-06-07", "SWAT"), ("2018-06-08", "SWAT"),
                           ("2018-07-05", "SWAT"), ("2018-07-06", "SWAT")))
    assert out["label"].tolist() == [False, True, True, False]


def test_precision_filter():
    assert not one("2021-06-01", "BEBS", classes={"alleged"}, precisions={"day"})["label"]


def test_min_confidence():
    assert not one("2018-06-20", "SWAT", min_confidence="A")["label"]
    assert one("2018-06-20", "SWAT", min_confidence="B")["label"]


def test_unknown_ticker_false():
    out = label_panel(bars(("2018-06-20", "ZZZZ")))
    r = out.iloc[0]
    assert not r["label"] and r["n_windows"] == 0
    assert pd.isna(r["window_id"]) and pd.isna(r["label_class"]) and pd.isna(r["confidence"])
    assert str(out["label"].dtype) == "boolean"
    assert str(out["n_windows"].dtype) == "Int64"
    assert str(out["window_id"].dtype) == "string"
    assert str(out["date"].dtype) == "datetime64[ns]"


def test_bad_filters_raise():
    b = bars(("2018-06-20", "SWAT"))
    with pytest.raises(ValueError):
        label_panel(b, classes={"nope"})
    with pytest.raises(ValueError):
        label_panel(b, precisions={"week"})
    with pytest.raises(ValueError):
        label_panel(b, min_confidence="Z")


def test_input_not_modified():
    b = bars(("2018-06-21", "SWAT"), ("2018-06-20", "SWAT"))
    before = b.copy(deep=True)
    out = label_panel(b)
    pd.testing.assert_frame_equal(b, before)
    assert out["date"].is_monotonic_increasing  # validate_bars order
