import json
from datetime import date

import pandas as pd
import pytest

from saham_gorengan.backfill import BackfillReport, backfill
from saham_gorengan.bars import BarsValidationError, validate_bars
from saham_gorengan.store import read_bars
from saham_gorengan.testing import synthetic_bars

START, END = date(2022, 1, 3), date(2022, 3, 31)


class FakeSource:
    name = "fake"

    def __init__(self, bad=(), n_tickers=3, start=START, end=END):
        self.frame = synthetic_bars(n_tickers=n_tickers, start=start, end=end)
        self.bad = set(bad)
        self.calls = []

    def fetch(self, tickers, start, end):
        self.calls.append(list(tickers))
        if self.bad & set(tickers):
            raise BarsValidationError("bad ticker in batch")
        f = self.frame
        m = (f["ticker"].isin(list(tickers)) & (f["date"] >= pd.Timestamp(start))
             & (f["date"] <= pd.Timestamp(end)))
        return validate_bars(f[m])


TICKERS = ["SYAA", "SYAB", "SYAC"]


def test_backfill_writes_months(tmp_path):
    src = FakeSource()
    rep = backfill(src, TICKERS, START, END, root=tmp_path, pause=0, sleep=lambda s: None)
    assert isinstance(rep, BackfillReport)
    assert rep.months_done == ["2022-01", "2022-02", "2022-03"]
    assert rep.months_skipped == [] and rep.failed == []
    assert len(list((tmp_path / "bars").glob("year=*/month=*/bars.parquet"))) == 3
    out = read_bars(START, END, root=tmp_path)
    assert rep.rows_written == len(out)
    pd.testing.assert_frame_equal(out.reset_index(drop=True), src.frame.reset_index(drop=True))


def test_resume_skips_complete_months(tmp_path):
    backfill(FakeSource(), TICKERS, START, END, root=tmp_path, sleep=lambda s: None)
    src = FakeSource()
    rep = backfill(src, TICKERS, START, END, root=tmp_path, sleep=lambda s: None)
    assert rep.months_skipped == ["2022-01", "2022-02", "2022-03"]
    assert rep.months_done == [] and rep.rows_written == 0
    assert src.calls == []


def test_changed_tickers_refetch(tmp_path):
    backfill(FakeSource(), TICKERS[:2], START, END, root=tmp_path, sleep=lambda s: None)
    src = FakeSource()
    rep = backfill(src, TICKERS, START, END, root=tmp_path, sleep=lambda s: None)
    assert rep.months_done == ["2022-01", "2022-02", "2022-03"]
    assert len(src.calls) == 3
    state = json.loads((tmp_path / "state" / "backfill.json").read_text())
    assert state["fake"]["complete"] == ["2022-01", "2022-02", "2022-03"]


def test_bad_ticker_isolated(tmp_path):
    src = FakeSource(bad={"SYAB"})
    rep = backfill(src, TICKERS, START, END, root=tmp_path, sleep=lambda s: None)
    assert [(m, t) for m, t, _ in rep.failed] == [("2022-01", "SYAB"), ("2022-02", "SYAB"),
                                                  ("2022-03", "SYAB")]
    assert all(msg for _, _, msg in rep.failed)
    out = read_bars(START, END, root=tmp_path)
    assert set(out["ticker"]) == {"SYAA", "SYAC"}
    assert rep.months_done == ["2022-01", "2022-02", "2022-03"]


def test_pause_between_calls(tmp_path):
    src = FakeSource(end=date(2022, 2, 28))
    sleeps = []
    backfill(src, TICKERS, date(2022, 1, 3), date(2022, 2, 28), root=tmp_path,
             batch_size=2, pause=0.5, sleep=sleeps.append)
    assert len(src.calls) == 4
    assert sleeps == [0.5, 0.5, 0.5]


def test_bad_args(tmp_path):
    with pytest.raises(ValueError):
        backfill(FakeSource(), TICKERS, END, START, root=tmp_path)
    with pytest.raises(ValueError):
        backfill(FakeSource(), [], START, END, root=tmp_path)


def test_corrupt_state_raises(tmp_path):
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "backfill.json").write_text("{nope")
    with pytest.raises(ValueError, match="backfill.json"):
        backfill(FakeSource(), TICKERS, START, END, root=tmp_path, sleep=lambda s: None)
