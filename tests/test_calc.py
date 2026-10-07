from __future__ import annotations

from datetime import datetime

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
