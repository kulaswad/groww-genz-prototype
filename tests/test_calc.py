from __future__ import annotations

from datetime import date, datetime

import pytest

from calc import (
    calculate_drawdown_metrics,
    calculate_sip_projection,
    stress_test_windows,
    xirr,
)


def test_xirr_simple_case_matches_10_percent():
    # 1000 invested on day 0, 1100 returned on day 365.
    # This is a true 365-day span: 2024-01-01 to 2024-12-31.
    cashflows = [
        (datetime(2024, 1, 1), -1000.0),
        (datetime(2024, 12, 31), 1100.0),
    ]
    assert xirr(cashflows) == pytest.approx(0.10, abs=1e-4)


def test_example_a_has_positive_xirr():
    # 3 monthly investments of 500 each, ending value 1782.56 after 3 months.
    # Total invested = 1500, value > invested, so the result must be positive.
    cashflows = [
        (datetime(2024, 1, 1), -500.0),
        (datetime(2024, 2, 1), -500.0),
        (datetime(2024, 3, 1), -500.0),
        (datetime(2024, 4, 1), 1782.56),
    ]
    assert xirr(cashflows) > 0.0


def test_drawdown_metrics_capture_both_peak_and_invested_shortfall():
    # Portfolio value peaks at 1080 then falls to 920.
    # Peak-to-trough fall = (1080 - 920) / 1080 = 0.148148...
    # At month 3, invested so far is 1000 and portfolio value is 920.
    # Shortfall vs invested = (1000 - 920) / 1000 = 0.08.
    metrics = calculate_drawdown_metrics(
        portfolio_values=[1000.0, 1080.0, 920.0, 1100.0],
        invested_values=[1000.0, 1000.0, 1000.0, 1000.0],
    )
    assert metrics["peak_to_trough_pct"] == pytest.approx(0.14814814814814814, abs=1e-9)
    assert metrics["invested_shortfall_pct"] == pytest.approx(0.08, abs=1e-9)


def test_sip_projection_includes_daily_timeline_and_drawdown_dates():
    nav_history = [
        {"date": "2024-01-01", "nav": 100.0},
        {"date": "2024-01-02", "nav": 120.0},
        {"date": "2024-01-03", "nav": 90.0},
        {"date": "2024-01-04", "nav": 80.0},
        {"date": "2024-01-05", "nav": 110.0},
    ]

    projection = calculate_sip_projection(
        amount=100.0,
        start_date="2024-01-01",
        nav_history=nav_history,
        months=1,
    )

    assert [item["portfolio_value"] for item in projection["timeline"]] == [100.0, 120.0, 90.0, 80.0, 110.0]
    assert projection["drawdown"]["peak_to_trough_peak_date"] == "2024-01-02"
    assert projection["drawdown"]["peak_to_trough_trough_date"] == "2024-01-04"
    assert projection["drawdown"]["invested_shortfall_point"]["date"] == "2024-01-04"


def test_sip_schedule_uses_next_available_nav_date_after_scheduled_instalment():
    # Scheduled instalment is Saturday 2024-03-02.
    # Because the market is closed on weekends, the next available NAV date is Monday 2024-03-04.
    nav_history = [
        {"date": "2024-03-01", "nav": 100.0},
        {"date": "2024-03-04", "nav": 101.0},
        {"date": "2024-03-05", "nav": 102.0},
    ]
    projection = calculate_sip_projection(
        amount=100.0,
        start_date="2024-03-02",
        nav_history=nav_history,
        months=1,
        as_of_date="2024-03-05",
    )
    assert projection["contributions"][0]["nav_date"] == "2024-03-04"


@pytest.mark.parametrize(
    ("year", "february_last_day"),
    [(2024, "2024-02-29"), (2023, "2023-02-28")],
)
def test_sip_schedule_clamps_day_31_to_month_end(year, february_last_day):
    # Hand arithmetic: min(31, 29) gives leap-year Feb 29; min(31, 28) gives
    # non-leap Feb 28; min(31, 30) gives Apr 30 in both years.
    expected_dates = [
        f"{year}-01-31",
        february_last_day,
        f"{year}-03-31",
        f"{year}-04-30",
    ]
    nav_history = [{"date": item, "nav": 100.0 + index} for index, item in enumerate(expected_dates)]

    projection = calculate_sip_projection(
        amount=100.0,
        start_date=date(year, 1, 31),
        nav_history=nav_history,
        months=4,
    )

    assert [item["date"] for item in projection["contributions"]] == expected_dates


def test_sip_projection_returns_controlled_result_when_tenure_exceeds_nav_history():
    nav_history = [
        {"date": date(2024, month, 5).isoformat(), "nav": 100.0}
        for month in range(1, 13)
    ]

    result = calculate_sip_projection(
        amount=500.0,
        start_date="2024-01-05",
        nav_history=nav_history,
        months=36,
        as_of_date="2024-12-05",
    )

    assert result["available"] is False
    assert "Not enough NAV history" in result["message"]


def test_stress_test_windows_returns_ranked_best_worst_selected_and_absolute_return_pct():
    nav_history = [
        {"date": "2024-01-01", "nav": 100.0},
        {"date": "2024-02-01", "nav": 110.0},
        {"date": "2024-03-01", "nav": 120.0},
        {"date": "2024-04-01", "nav": 130.0},
    ]
    result = stress_test_windows(
        amount=500.0,
        tenure_months=2,
        nav_history=nav_history,
        selected_window=("2024-01-01", "2024-03-01"),
    )
    assert "best" in result
    assert "worst" in result
    assert "selected" in result
    assert "windows" in result
    assert "absolute_return_pct" in result["selected"]
