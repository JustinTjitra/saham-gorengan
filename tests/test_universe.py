from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from saham_gorengan.universe import active_on, fetch_plan, load_universe

FIXTURE = Path(__file__).parent / "fixtures" / "universe_sample.csv"
HEADER = "ticker,listed,delisted,source\n"


def test_load_sample():
    u = load_universe(FIXTURE)
    assert len(u) == 4
    assert list(u.columns) == ["ticker", "listed", "delisted", "source"]
    assert pd.api.types.is_datetime64_ns_dtype(u["listed"])
    assert pd.api.types.is_datetime64_ns_dtype(u["delisted"])
    assert pd.api.types.is_string_dtype(u["ticker"])
    assert pd.api.types.is_string_dtype(u["source"])
    nat = u.set_index("ticker")["delisted"].isna()
    assert nat["AAAA"] and nat["CCCC"] and not nat["BBBB"] and not nat["DDDD"]


def test_active_on():
    u = load_universe(FIXTURE)
    assert active_on(u, date(2020, 1, 2)) == ["AAAA", "BBBB"]
    assert active_on(u, date(2021, 3, 15)) == ["AAAA", "BBBB"]
    assert active_on(u, date(2021, 3, 16)) == ["AAAA"]


def test_fetch_plan():
    u = load_universe(FIXTURE)
    p = fetch_plan(u, date(2016, 1, 1), date(2024, 12, 31))
    assert list(p.columns) == ["ticker", "start", "end"]
    assert list(p["ticker"]) == ["AAAA", "BBBB"]
    assert list(p["start"]) == [pd.Timestamp("2016-01-01"), pd.Timestamp("2018-05-02")]
    assert list(p["end"]) == [pd.Timestamp("2024-12-31"), pd.Timestamp("2021-03-15")]
    assert pd.api.types.is_datetime64_ns_dtype(p["start"])
    with pytest.raises(ValueError):
        fetch_plan(u, date(2024, 1, 1), date(2023, 1, 1))


@pytest.mark.parametrize(
    "body, line",
    [
        ("ticker,listed,source\nAAAA,2010-01-04,x\n", "line 1"),
        (HEADER + "aaaa,2010-01-04,,x\n", "line 2"),
        (HEADER + "AAAAA,2010-01-04,,x\n", "line 2"),
        (HEADER + "AAAA,2010-01-04,,x\nBBBB,2010-01-04,2009-01-01,x\n", "line 3"),
        (HEADER + "AAAA,2010-01-04,,x\nAAAA,2011-01-04,,x\n", "line 3"),
        (HEADER + "AAAA,2010-01-04,,\n", "line 2"),
        (HEADER + "AAAA,2010-01-04,x\n", "line 2"),
        (HEADER + "AAAA,2010-13-04,,x\n", "line 2"),
    ],
)
def test_validation(tmp_path, body, line):
    f = tmp_path / "u.csv"
    f.write_text(body, encoding="utf-8")
    with pytest.raises(ValueError, match=line):
        load_universe(f)


def test_excel_bom_header(tmp_path):
    # Excel's "CSV UTF-8" export starts with a byte-order mark; the owner's file may come from Excel.
    p = tmp_path / "bom.csv"
    p.write_text("ticker,listed,delisted,source\nAAAA,2010-01-04,,test fixture\n", encoding="utf-8-sig")
    assert load_universe(p)["ticker"].tolist() == ["AAAA"]
