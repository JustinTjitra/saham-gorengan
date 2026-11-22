"""Tests for the `saham-gorengan score` command (P6-01)."""
from __future__ import annotations

import io
from datetime import date

import pandas as pd
import pytest

from saham_gorengan.cli import main, score_day
from saham_gorengan.store import write_bars
from saham_gorengan.testing import Pump, synthetic_bars

DAYS = pd.bdate_range("2024-01-02", "2024-12-31")
PUMP_START = DAYS[150].date()
SCORE_DAY = DAYS[155].date()
PUMP_TICKER = "SYAC"


@pytest.fixture(scope="module")
def bars():
    return synthetic_bars(n_tickers=30, start=date(2024, 1, 2), end=date(2024, 12, 31), seed=0,
                          pumps=[Pump(ticker=PUMP_TICKER, start=PUMP_START)])


@pytest.fixture()
def store(tmp_path, bars):
    write_bars(bars, root=tmp_path)
    return tmp_path


def test_score_day_topk(store):
    out = score_day(SCORE_DAY, root=store, k=10)
    assert list(out.columns) == ["date", "ticker", "rank", "score"]
    assert 0 < len(out) <= 10
    assert out["rank"].tolist() == list(range(1, len(out) + 1))
    assert str(out["rank"].dtype) == "Int64" and out["score"].dtype == "float64"
    assert (out["date"] == pd.Timestamp(SCORE_DAY)).all()
    assert int(out.loc[out["ticker"] == PUMP_TICKER, "rank"].iloc[0]) <= 3


def test_no_lookahead(tmp_path_factory, bars):
    full, trunc = tmp_path_factory.mktemp("full"), tmp_path_factory.mktemp("trunc")
    write_bars(bars, root=full)
    write_bars(bars[bars["date"] <= pd.Timestamp(SCORE_DAY)], root=trunc)
    a = score_day(SCORE_DAY, root=full)
    b = score_day(SCORE_DAY, root=trunc)
    pd.testing.assert_frame_equal(a, b)


def test_missing_day(store):
    with pytest.raises(ValueError, match="no bars"):
        score_day(date(2024, 6, 15), root=store)  # a Saturday


def test_main_csv(store, capsys):
    assert main(["score", "--date", SCORE_DAY.isoformat(), "--data-dir", str(store), "--k", "5"]) == 0
    out = capsys.readouterr().out
    df = pd.read_csv(io.StringIO(out))
    assert list(df.columns) == ["date", "ticker", "rank", "score"]
    assert len(df) == 5
    assert (df["date"] == SCORE_DAY.isoformat()).all()


def test_main_error(store, capsys):
    assert main(["score", "--date", "2024-06-15", "--data-dir", str(store)]) == 2
    cap = capsys.readouterr()
    assert cap.err.startswith("error:") and "no bars" in cap.err
    assert cap.out == ""


def test_no_subcommand(capsys):
    assert main([]) == 2


def test_bad_args(store):
    with pytest.raises(ValueError):
        score_day(SCORE_DAY, root=store, k=0)
    with pytest.raises(ValueError):
        score_day(SCORE_DAY, root=store, history_days=10)
