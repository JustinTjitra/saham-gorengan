import pandas as pd
import pytest

from saham_gorengan.bars import BAR_COLUMNS, BarsValidationError, empty_bars, validate_bars

OPTIONAL = ["adj_close", "value", "frequency", "foreign_buy", "foreign_sell",
            "listed_shares", "tradeable_shares"]


def make(**over):
    df = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-02"]),
        "ticker": ["BBCA", "BBCA", "GOTO"],
        "open": [10.0, 11.0, 5.0],
        "high": [12.0, 12.0, 6.0],
        "low": [9.0, 10.0, 4.0],
        "close": [11.0, 11.5, 5.5],
        "volume": [100.0, 0.0, float("nan")],
        "source": ["t", "t", "t"],
    })
    for k, v in over.items():
        df[k] = v
    return df


def test_valid_roundtrip():
    out = validate_bars(make())
    assert list(out.columns) == list(BAR_COLUMNS)
    assert {c: str(t) for c, t in out.dtypes.items()} == BAR_COLUMNS
    assert list(out["ticker"]) == ["BBCA", "GOTO", "BBCA"]
    assert list(out.index) == [0, 1, 2]


def test_input_not_modified():
    df = make()
    before = df.copy()
    validate_bars(df)
    pd.testing.assert_frame_equal(df, before)


def test_empty_bars_valid():
    e = empty_bars()
    assert len(e) == 0
    assert {c: str(t) for c, t in e.dtypes.items()} == BAR_COLUMNS
    out = validate_bars(e)
    assert {c: str(t) for c, t in out.dtypes.items()} == BAR_COLUMNS


def test_optional_filled_with_nulls():
    out = validate_bars(make())
    for c in OPTIONAL:
        assert out[c].isna().all()


def test_missing_required_raises():
    with pytest.raises(BarsValidationError, match="close"):
        validate_bars(make().drop(columns=["close"]))


def test_extra_column_raises():
    with pytest.raises(BarsValidationError, match="bogus"):
        validate_bars(make(bogus=1))


def test_duplicates():
    df = make(ticker=["BBCA", "BBCA", "GOTO"], date=pd.to_datetime(["2024-01-02"] * 3))
    with pytest.raises(BarsValidationError, match="duplicate"):
        validate_bars(df)


def test_bad_ticker():
    with pytest.raises(BarsValidationError, match="ticker"):
        validate_bars(make(ticker=["BBCA", "bbca", "GOTO1"]))


@pytest.mark.parametrize("col", ["open", "high", "low", "close"])
def test_non_positive_price(col):
    df = make()
    df.loc[0, col] = 0.0
    with pytest.raises(BarsValidationError, match="non-positive"):
        validate_bars(df)


def test_nan_price():
    df = make()
    df.loc[0, "close"] = float("nan")
    with pytest.raises(BarsValidationError, match="missing price"):
        validate_bars(df)


def test_high_too_low():
    df = make()
    df.loc[0, "high"] = 10.5  # below close 11
    with pytest.raises(BarsValidationError, match="high below"):
        validate_bars(df)


def test_low_too_high():
    df = make()
    df.loc[0, "low"] = 10.5  # above open 10
    with pytest.raises(BarsValidationError, match="low above"):
        validate_bars(df)


@pytest.mark.parametrize("col", ["volume", "value", "frequency"])
def test_negative(col):
    df = make()
    df[col] = [-1, 1, 1]
    with pytest.raises(BarsValidationError, match=f"negative {col}"):
        validate_bars(df)


def test_time_component():
    df = make(date=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-02"]) + pd.to_timedelta([10, 0, 0], unit="h"))
    with pytest.raises(BarsValidationError, match="time component"):
        validate_bars(df)


def test_timezone():
    df = make(date=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-02"]).tz_localize("UTC"))
    with pytest.raises(BarsValidationError, match="timezone"):
        validate_bars(df)


def test_coercion_failure():
    with pytest.raises(BarsValidationError, match="close"):
        validate_bars(make(close=["x", "1", "2"]))


def test_two_problems_both_reported():
    df = make(ticker=["BBCA", "bbca", "GOTO"])
    df.loc[0, "open"] = -1.0
    with pytest.raises(BarsValidationError) as e:
        validate_bars(df)
    assert "ticker" in str(e.value) and "non-positive" in str(e.value)


def test_missing_date_and_source():
    df = make(date=[pd.Timestamp("2024-01-02"), pd.NaT, pd.Timestamp("2024-01-02")],
              source=["t", None, "t"])
    with pytest.raises(BarsValidationError) as exc:
        validate_bars(df)
    assert "missing date" in str(exc.value)
    assert "missing source" in str(exc.value)
