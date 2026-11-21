from datetime import date
from pathlib import Path

import pytest

from saham_gorengan.surveillance import (
    SurveillanceEvent,
    classify_suspension_reason,
    load_surveillance_events,
)

FIXTURE = Path(__file__).parent / "fixtures" / "surveillance_events.csv"
HEADER = "date,ticker,event_type,reason_class,source,source_url,notes"
GOOD = "2024-03-05,AAAA,uma,,idx_announcement,https://example.com/x,synthetic fixture"


def _write(tmp_path, *lines, header=HEADER):
    p = tmp_path / "events.csv"
    p.write_text("\n".join([header, *lines]) + "\n", encoding="utf-8")
    return p


def test_load_fixture():
    events = load_surveillance_events(FIXTURE)
    assert all(isinstance(e, SurveillanceEvent) for e in events)
    keys = [(e.date, e.ticker, e.event_type) for e in events]
    assert keys == sorted(keys)
    assert {"uma", "suspension", "suspension_lifted", "watchlist_entry"} <= {e.event_type for e in events}
    susp = [e for e in events if e.event_type == "suspension"]
    assert susp and all(e.reason_class is not None for e in susp)
    assert any(e.reason_class == "price_up" for e in susp)
    uma = [e for e in events if e.event_type == "uma"]
    assert uma and all(e.reason_class is None for e in uma)
    assert events[0].date == date(2024, 3, 5)


def test_bad_header(tmp_path):
    p = _write(tmp_path, GOOD, header="date,ticker,event_type,source,source_url,notes")
    with pytest.raises(ValueError, match="line 1"):
        load_surveillance_events(p)


@pytest.mark.parametrize("row", [
    "2024-03-05,AAAA,bogus,,idx_announcement,https://example.com/x,n",
    "2024-03-05,AAAA,suspension,bogus,idx_announcement,https://example.com/x,n",
    "2024-03-05,AAAA,uma,,bogus,https://example.com/x,n",
])
def test_unknown_enum(tmp_path, row):
    with pytest.raises(ValueError, match="line 3"):
        load_surveillance_events(_write(tmp_path, GOOD.replace("AAAA", "BBBB"), row))


@pytest.mark.parametrize("ticker", ["aaaa", "AAA", "AAAAA", "AAA1", ""])
def test_bad_ticker(tmp_path, ticker):
    row = f"2024-03-05,{ticker},uma,,idx_announcement,https://example.com/x,n"
    with pytest.raises(ValueError, match="line 2"):
        load_surveillance_events(_write(tmp_path, row))


def test_empty_source_url(tmp_path):
    with pytest.raises(ValueError, match="line 2"):
        load_surveillance_events(_write(tmp_path, "2024-03-05,AAAA,uma,,idx_announcement, ,n"))


def test_reason_class_on_non_suspension(tmp_path):
    with pytest.raises(ValueError, match="line 2"):
        load_surveillance_events(
            _write(tmp_path, "2024-03-05,AAAA,uma,price_up,idx_announcement,https://example.com/x,n")
        )


def test_reason_class_missing_on_suspension(tmp_path):
    with pytest.raises(ValueError, match="line 2"):
        load_surveillance_events(
            _write(tmp_path, "2024-03-05,AAAA,suspension,,idx_announcement,https://example.com/x,n")
        )


def test_duplicate_rows(tmp_path):
    with pytest.raises(ValueError, match=r"line 3.*line 2|line 2.*line 3"):
        load_surveillance_events(_write(tmp_path, GOOD, GOOD))


@pytest.mark.parametrize("text, expected", [
    ("Peningkatan harga kumulatif yang signifikan ... dalam rangka cooling down", "price_up"),
    ("penurunan harga kumulatif yang signifikan", "price_down"),
    ("dalam rangka Cooling Down sebagai bentuk perlindungan bagi investor", "cooling_down"),
    ("Keterlambatan penyampaian Laporan Keuangan", "late_filing"),
    ("belum melakukan pembayaran Biaya Pencatatan Tahunan", "listing_fee"),
    ("Belum memenuhi ketentuan V.1.1. peraturan bursa nomor I-A", "free_float"),
    ("keraguan atas kelangsungan usaha", "going_concern"),
    ("aksi korporasi", "non_price_other"),
    ("", "unknown"),
    ("   \n\t ", "unknown"),
    ("cooling\n  down", "cooling_down"),
])
def test_classify_examples(text, expected):
    assert classify_suspension_reason(text) == expected


def test_i_a_needs_word_boundary():
    assert classify_suspension_reason("via-alpha") != "free_float"
