import pytest

from saham_gorengan import _load
from saham_gorengan._load import _rows, data_dir


def _write(tmp_path, monkeypatch, text, name="t.csv"):
    (tmp_path / name).write_text(text, encoding="utf-8")
    monkeypatch.setattr(_load, "data_dir", lambda: tmp_path)
    return name


def test_rows_reads_well_formed_file(tmp_path, monkeypatch):
    name = _write(tmp_path, monkeypatch, "a,b\n1,2\n")
    assert _rows(name) == [{"a": "1", "b": "2"}]


def test_rows_rejects_extra_field(tmp_path, monkeypatch):
    name = _write(tmp_path, monkeypatch, "a,b\n1,2,3\n")
    with pytest.raises(ValueError) as exc:
        _rows(name)
    assert "line 2" in str(exc.value)
    assert name in str(exc.value)


def test_rows_rejects_missing_field(tmp_path, monkeypatch):
    name = _write(tmp_path, monkeypatch, "a,b\n1\n")
    with pytest.raises(ValueError):
        _rows(name)


def test_rows_quoted_comma_is_fine(tmp_path, monkeypatch):
    name = _write(tmp_path, monkeypatch, 'a,b\n1,"x, y"\n')
    assert _rows(name)[0]["b"] == "x, y"


def test_rows_blank_trailing_lines_ok(tmp_path, monkeypatch):
    name = _write(tmp_path, monkeypatch, "a,b\n1,2\n\n\n")
    assert _rows(name) == [{"a": "1", "b": "2"}]


def test_all_shipped_csvs_are_well_formed():
    files = sorted(data_dir().glob("*.csv"))
    assert files
    for p in files:
        _rows(p.name)
