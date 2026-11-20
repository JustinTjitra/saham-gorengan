from datetime import date
from pathlib import Path

import pandas as pd
import pytest

import saham_gorengan
from saham_gorengan.bars import empty_bars, validate_bars
from saham_gorengan.store import read_bars, store_root, write_bars


def make(dates, tickers=("BBCA",), close=10.0, source="t"):
    rows = []
    for d in dates:
        for t in tickers:
            rows.append({"date": pd.Timestamp(d), "ticker": t, "open": 10.0, "high": 12.0,
                         "low": 9.0, "close": close, "volume": 100.0, "source": source})
    return pd.DataFrame(rows)


def test_roundtrip(tmp_path):
    df = validate_bars(make(["2024-01-02", "2024-01-03"], ("BBCA", "GOTO")))
    files = write_bars(df, tmp_path)
    assert files == [tmp_path / "bars" / "year=2024" / "month=01" / "bars.parquet"]
    out = read_bars(date(2024, 1, 1), date(2024, 1, 31), root=tmp_path)
    pd.testing.assert_frame_equal(out, df)


def test_two_months_two_files(tmp_path):
    files = write_bars(make(["2024-01-31", "2024-02-01"]), tmp_path)
    assert len(files) == 2
    assert all(f.exists() for f in files)
    assert files[1].parent.name == "month=02"
    assert not list(tmp_path.rglob("*.tmp-*"))


def test_overwrite_replaces_overlap(tmp_path):
    write_bars(make(["2024-01-02", "2024-01-03"], close=10.0, source="old"), tmp_path)
    write_bars(make(["2024-01-03", "2024-01-04"], close=11.0, source="new"), tmp_path)
    out = read_bars(date(2024, 1, 1), date(2024, 1, 31), root=tmp_path)
    assert list(out["date"].dt.day) == [2, 3, 4]
    assert list(out["source"]) == ["old", "new", "new"]
    assert list(out["close"]) == [10.0, 11.0, 11.0]


def test_filters(tmp_path):
    write_bars(make(["2024-01-02", "2024-01-15", "2024-02-05"], ("BBCA", "GOTO")), tmp_path)
    out = read_bars(date(2024, 1, 10), date(2024, 2, 5), ["GOTO"], root=tmp_path)
    assert list(out["ticker"]) == ["GOTO", "GOTO"]
    assert list(out["date"].dt.strftime("%m-%d")) == ["01-15", "02-05"]
    assert read_bars(date(2025, 1, 1), date(2025, 2, 1), root=tmp_path).empty


def test_empty_cases(tmp_path):
    assert write_bars(empty_bars(), tmp_path) == []
    out = read_bars(date(2024, 1, 1), date(2024, 1, 31), root=tmp_path)
    pd.testing.assert_frame_equal(out, empty_bars())
    with pytest.raises(ValueError):
        read_bars(date(2024, 2, 1), date(2024, 1, 1), root=tmp_path)


def test_missing_root_raises(monkeypatch):
    monkeypatch.delenv("SAHAM_DATA_DIR", raising=False)
    with pytest.raises(RuntimeError):
        store_root()


def test_env_var_used(monkeypatch, tmp_path):
    monkeypatch.setenv("SAHAM_DATA_DIR", str(tmp_path))
    assert store_root() == tmp_path.resolve()


def test_root_inside_repo_raises():
    repo = Path(saham_gorengan.__file__).resolve()
    while not (repo / ".git").exists():
        repo = repo.parent
    with pytest.raises(RuntimeError):
        store_root(repo / "data")
    with pytest.raises(RuntimeError):
        store_root(repo / "store" / ".." / "src")
    assert store_root(repo / "store") == repo / "store"
    assert store_root(repo / "store" / "x") == repo / "store" / "x"
