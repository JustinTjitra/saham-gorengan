from datetime import date

import pytest

from saham_gorengan import labels_on, price_limits


# --- price_limits: every regime switch, checked on both sides ---------------

@pytest.mark.parametrize(
    "day, price, ara, arb",
    [
        (date(2016, 6, 1), 100, 35, 10),     # 2015 asymmetric, lowest tier
        (date(2017, 1, 2), 1000, 25, 10),    # last day before symmetric
        (date(2017, 1, 3), 1000, 25, 25),    # symmetric starts
        (date(2020, 3, 9), 6000, 20, 20),
        (date(2020, 3, 10), 6000, 20, 10),   # COVID ARB 10%
        (date(2020, 3, 12), 6000, 20, 10),
        (date(2020, 3, 13), 6000, 20, 7),    # ARB 7%
        (date(2023, 6, 4), 150, 35, 7),
        (date(2023, 6, 5), 150, 35, 15),     # stage I
        (date(2023, 9, 3), 150, 35, 15),
        (date(2023, 9, 4), 150, 35, 35),     # stage II symmetric
        (date(2025, 4, 7), 150, 35, 35),
        (date(2025, 4, 8), 150, 35, 15),     # tariff shock
        (date(2026, 11, 9), 150, 35, 15),    # open-ended regime
    ],
)
def test_price_limits_by_date(day, price, ara, arb):
    limits = price_limits(day, price)
    assert (limits.ara_pct, limits.arb_pct) == (ara, arb)


@pytest.mark.parametrize(
    "price, ara",
    [(50, 35), (200, 35), (201, 25), (5000, 25), (5001, 20), (100_000, 20)],
)
def test_price_tier_boundaries(price, ara):
    # Tier bounds: Rp50-200, >200-5,000, >5,000 (upper bound inclusive).
    assert price_limits(date(2024, 1, 2), price).ara_pct == ara


def test_price_limits_reports_regime():
    assert price_limits(date(2021, 1, 4), 500).regime_id == "R2020-ARB7"


def test_price_limits_before_coverage_raises():
    with pytest.raises(ValueError, match="before"):
        price_limits(date(2015, 8, 21), 1000)


def test_price_limits_rejects_non_positive_price():
    with pytest.raises(ValueError):
        price_limits(date(2024, 1, 2), 0)


# --- labels_on ----------------------------------------------------------------

def test_labels_on_inside_window_inclusive_bounds():
    assert [w.window_id for w in labels_on("PANR", date(2022, 9, 6))] == ["PANR-2022-1"]
    assert [w.window_id for w in labels_on("PANR", date(2023, 5, 29))] == ["PANR-2022-1"]
    assert labels_on("PANR", date(2023, 5, 30)) == []


def test_labels_on_gap_between_dssa_windows():
    assert labels_on("DSSA", date(2024, 7, 16)) == []
    assert labels_on("DSSA", date(2024, 7, 18))


def test_labels_on_ticker_is_case_insensitive():
    assert labels_on("panr", date(2022, 12, 1))


def test_alleged_cases_are_excluded_by_default():
    assert labels_on("SWAT", date(2018, 6, 20)) == []
    assert labels_on("SWAT", date(2018, 6, 20), classes={"alleged"})


def test_filter_by_precision():
    assert labels_on("KIOS", date(2021, 6, 1))
    assert labels_on("KIOS", date(2021, 6, 1), precisions={"day"}) == []


def test_filter_by_confidence():
    assert labels_on("SUPR", date(2022, 3, 1))
    assert labels_on("SUPR", date(2022, 3, 1), min_confidence="B") == []
    assert labels_on("PANR", date(2022, 12, 1), min_confidence="A")


def test_film_has_two_separate_cases():
    assert [w.case_id for w in labels_on("FILM", date(2021, 6, 1))] == ["BVN-2021"]
    assert [w.case_id for w in labels_on("FILM", date(2023, 5, 1))] == ["FILM-2023"]


def test_invalid_filter_values_raise():
    with pytest.raises(ValueError):
        labels_on("PANR", date(2022, 12, 1), classes={"sanctionedd"})
    with pytest.raises(ValueError):
        labels_on("PANR", date(2022, 12, 1), min_confidence="D")
