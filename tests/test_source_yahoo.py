"""Offline tests for the Yahoo adapter: yfinance is replaced by a fake module."""
import sys
import types
from datetime import date

import numpy as np
import pandas as pd
import pytest

from saham_gorengan.bars import validate_bars
from saham_gorengan.sources import SourceError, YahooSource

FIELDS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
IDX = pd.DatetimeIndex(["2024-01-02", "2024-01-03"], name="Date")


def _one(base: float) -> pd.DataFrame:
    return pd.DataFrame(
        {"Open": [base, base + 1], "High": [base + 2, base + 3], "Low": [base - 1, base],
         "Close": [base + 1, base + 2], "Adj Close": [base + 0.5, base + 1.5],
         "Volume": [1000.0, 2000.0]}, index=IDX)


def _multi(frames: dict) -> pd.DataFrame:
    return pd.concat(frames, axis=1)


def _fake(results):
    """results: list of DataFrames or exceptions returned/raised per call."""
    mod = types.ModuleType("yfinance")
    mod.calls = []
    queue = list(results)

    def download(*args, **kwargs):
        mod.calls.append((args, kwargs))
        item = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(item, Exception):
            raise item
        return item

    mod.download = download
    return mod


class YFRateLimitError(Exception):
    pass


def _src(sleeps=None, **kw):
    sleeps = sleeps if sleeps is not None else []
    return YahooSource(sleep=sleeps.append, **kw)


def test_two_tickers_multiindex(monkeypatch):
    fake = _fake([_multi({"BBCA.JK": _one(100.0), "TLKM.JK": _one(50.0)})])
    monkeypatch.setitem(sys.modules, "yfinance", fake)
    out = _src().fetch(["bbca", " TLKM "], date(2024, 1, 2), date(2024, 1, 3))
    validate_bars(out)
    assert set(out["ticker"]) == {"BBCA", "TLKM"}
    assert len(out) == 4
    row = out[(out.ticker == "BBCA") & (out.date == "2024-01-02")].iloc[0]
    assert row["adj_close"] == 100.5 and row["close"] == 101.0
    assert (out["source"] == "yahoo").all()
    assert out[["value", "frequency", "foreign_buy", "listed_shares"]].isna().all().all()


def test_flat_single_ticker(monkeypatch):
    fake = _fake([_one(100.0)])
    monkeypatch.setitem(sys.modules, "yfinance", fake)
    out = _src().fetch(["BBCA"], date(2024, 1, 2), date(2024, 1, 3))
    validate_bars(out)
    assert list(out["ticker"].unique()) == ["BBCA"]
    assert out["adj_close"].notna().all()


def test_call_arguments(monkeypatch):
    fake = _fake([_multi({"BBCA.JK": _one(100.0)})])
    monkeypatch.setitem(sys.modules, "yfinance", fake)
    _src().fetch(["BBCA"], date(2024, 1, 2), date(2024, 1, 3))
    args, kw = fake.calls[0]
    assert kw["auto_adjust"] is False
    assert kw["end"] == date(2024, 1, 4)
    assert kw["start"] == date(2024, 1, 2)
    assert kw["interval"] == "1d" and kw["group_by"] == "ticker"
    assert kw["actions"] is False and kw["progress"] is False and kw["threads"] is False
    symbols = kw.get("tickers", args[0] if args else None)
    assert list(symbols) == ["BBCA.JK"]


def test_all_nan_ticker_dropped(monkeypatch, caplog):
    dead = pd.DataFrame(np.nan, index=IDX, columns=FIELDS)
    fake = _fake([_multi({"BBCA.JK": _one(100.0), "ZZZZ.JK": dead})])
    monkeypatch.setitem(sys.modules, "yfinance", fake)
    with caplog.at_level("INFO"):
        out = _src().fetch(["BBCA", "ZZZZ"], date(2024, 1, 2), date(2024, 1, 3))
    assert set(out["ticker"]) == {"BBCA"}
    assert "ZZZZ" in caplog.text


def test_empty_frame(monkeypatch):
    fake = _fake([pd.DataFrame()])
    monkeypatch.setitem(sys.modules, "yfinance", fake)
    out = _src().fetch(["BBCA"], date(2024, 1, 2), date(2024, 1, 3))
    assert out.empty and "adj_close" in out.columns


def test_tz_aware_index(monkeypatch):
    df = _one(100.0)
    df.index = df.index.tz_localize("Asia/Jakarta")
    monkeypatch.setitem(sys.modules, "yfinance", _fake([_multi({"BBCA.JK": df})]))
    out = _src().fetch(["BBCA"], date(2024, 1, 2), date(2024, 1, 3))
    assert list(out["date"]) == list(pd.to_datetime(["2024-01-02", "2024-01-03"]))


def test_rate_limit_retries(monkeypatch):
    good = _multi({"BBCA.JK": _one(100.0)})
    fake = _fake([YFRateLimitError("x"), YFRateLimitError("x"), good])
    monkeypatch.setitem(sys.modules, "yfinance", fake)
    sleeps: list = []
    out = _src(sleeps).fetch(["BBCA"], date(2024, 1, 2), date(2024, 1, 3))
    assert sleeps == [2.0, 4.0]
    assert len(out) == 2


def test_connection_error_retried(monkeypatch):
    good = _multi({"BBCA.JK": _one(100.0)})
    monkeypatch.setitem(sys.modules, "yfinance", _fake([ConnectionError("x"), good]))
    sleeps: list = []
    _src(sleeps).fetch(["BBCA"], date(2024, 1, 2), date(2024, 1, 3))
    assert sleeps == [2.0]


def test_retries_exhausted(monkeypatch):
    err = YFRateLimitError("slow down")
    monkeypatch.setitem(sys.modules, "yfinance", _fake([err]))
    sleeps: list = []
    with pytest.raises(SourceError) as ei:
        _src(sleeps).fetch(["BBCA"], date(2024, 1, 2), date(2024, 1, 3))
    assert sleeps == [2.0, 4.0, 8.0, 16.0, 32.0]
    assert ei.value.__cause__ is err


def test_non_retryable_propagates(monkeypatch):
    monkeypatch.setitem(sys.modules, "yfinance", _fake([KeyError("boom")]))
    sleeps: list = []
    with pytest.raises(KeyError):
        _src(sleeps).fetch(["BBCA"], date(2024, 1, 2), date(2024, 1, 3))
    assert sleeps == []


def test_missing_module(monkeypatch):
    monkeypatch.setitem(sys.modules, "yfinance", None)
    with pytest.raises(SourceError, match=r"pip install saham-gorengan\[yahoo\]"):
        _src().fetch(["BBCA"], date(2024, 1, 2), date(2024, 1, 3))


def test_input_validation(monkeypatch):
    fake = _fake([pd.DataFrame()])
    monkeypatch.setitem(sys.modules, "yfinance", fake)
    with pytest.raises(ValueError):
        _src().fetch(["BBCA1"], date(2024, 1, 2), date(2024, 1, 3))
    with pytest.raises(ValueError):
        _src().fetch(["BBCA"], date(2024, 1, 5), date(2024, 1, 3))
    assert fake.calls == []
