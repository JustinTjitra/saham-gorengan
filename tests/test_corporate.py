import pandas as pd

from saham_gorengan.corporate import corporate_action_suspects


def _bar(date, close, adj=None, ticker="AAAA"):
    row = {"date": date, "ticker": ticker, "open": close, "high": close, "low": close,
           "close": close, "volume": 100.0, "source": "test"}
    if adj is not None:
        row["adj_close"] = adj
    return row


def _pair(prev_close, close, adj=None, prev_adj=None):
    return pd.DataFrame([_bar("2024-01-02", prev_close, prev_adj), _bar("2024-01-03", close, adj)])


def test_split_detected():
    r = corporate_action_suspects(_pair(1000.0, 200.0)).iloc[-1]
    assert r["suspect"] is True or r["suspect"] == True  # noqa: E712
    assert r["kind"] == "split"
    assert r["price_ratio"] == 5.0


def test_reverse_split_detected():
    r = corporate_action_suspects(_pair(100.0, 1000.0)).iloc[-1]
    assert r["suspect"] == True  # noqa: E712
    assert r["kind"] == "reverse_split"


def test_normal_day_not_suspect():
    r = corporate_action_suspects(_pair(100.0, 110.0, adj=110.0, prev_adj=100.0)).iloc[-1]
    assert r["suspect"] == False  # noqa: E712
    assert pd.isna(r["kind"])


def test_adj_factor_jump():
    r = corporate_action_suspects(_pair(100.0, 100.0, adj=90.0, prev_adj=100.0)).iloc[-1]
    assert r["suspect"] == True  # noqa: E712
    assert r["kind"] == "unknown"


def test_small_dividend_not_flagged():
    r = corporate_action_suspects(_pair(100.0, 100.0, adj=98.0, prev_adj=100.0)).iloc[-1]
    assert r["suspect"] == False  # noqa: E712
    assert pd.isna(r["kind"])


def test_first_bar_na():
    out = corporate_action_suspects(pd.DataFrame([_bar("2024-01-02", 100.0)]))
    assert pd.isna(out["suspect"].iloc[0])
    assert pd.isna(out["price_ratio"].iloc[0])
    assert pd.isna(out["kind"].iloc[0])


def test_output_shape_and_dtypes():
    out = corporate_action_suspects(_pair(1000.0, 200.0))
    assert list(out.columns) == ["date", "ticker", "suspect", "price_ratio", "kind"]
    assert str(out["date"].dtype) == "datetime64[ns]"
    assert str(out["ticker"].dtype) == "string"
    assert str(out["suspect"].dtype) == "boolean"
    assert str(out["price_ratio"].dtype) == "float64"
    assert str(out["kind"].dtype) == "string"
    assert isinstance(out.index, pd.RangeIndex)


def test_input_not_modified():
    df = _pair(1000.0, 200.0)
    before = df.copy(deep=True)
    corporate_action_suspects(df)
    pd.testing.assert_frame_equal(df, before)
