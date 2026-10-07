from __future__ import annotations

from datetime import date, datetime

import pytest

from calc import (
    calculate_drawdown_metrics,
    calculate_sip_projection,
    analyze_largest_nav_fall,
    convert_habit_to_monthly_amount,
    stress_test_windows,
    stress_test_window_count,
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


def test_largest_nav_fall_tracks_lump_sum_value_and_recovery():
    # The high is 120 on Jan 2; the trough is 80 on Jan 4.
    # Fall = (120 - 80) / 120 = 33.33%; Rs 10,000 becomes Rs 6,666.67.
    # Recovery is Jan 6, two calendar days after the trough; latest value is 10,000 * 130 / 120.
    nav_history = [
        {"date": "2024-01-01", "nav": 100},
        {"date": "2024-01-02", "nav": 120},
        {"date": "2024-01-03", "nav": 90},
        {"date": "2024-01-04", "nav": 80},
        {"date": "2024-01-05", "nav": 110},
        {"date": "2024-01-06", "nav": 120},
        {"date": "2024-01-07", "nav": 130},
    ]

    result = analyze_largest_nav_fall(nav_history)

    assert result["peak_date"] == "2024-01-02"
    assert result["trough_date"] == "2024-01-04"
    assert result["fall_pct"] == pytest.approx(1 / 3)
    assert result["trough_value"] == pytest.approx(6_666.6666667)
    assert result["recovery_date"] == "2024-01-06"
    assert result["recovery_days"] == 2
    assert result["latest_value"] == pytest.approx(10_833.3333333)
    assert result["history"] == [
        {"date": "2024-01-02", "value": 10_000.0},
        {"date": "2024-01-03", "value": 7_500.0},
        {"date": "2024-01-04", "value": pytest.approx(6_666.6666667)},
    ]


def test_largest_nav_fall_reports_when_recovery_did_not_happen():
    # The peak is 120 and all later NAVs stay below 120, so no recovery is recorded.
    nav_history = [
        {"date": "2024-01-01", "nav": 100},
        {"date": "2024-01-02", "nav": 120},
        {"date": "2024-01-03", "nav": 80},
        {"date": "2024-01-04", "nav": 110},
    ]

    result = analyze_largest_nav_fall(nav_history)

    assert result["recovery_date"] is None
    assert result["recovery_days"] is None


@pytest.mark.parametrize(
    ("amount", "frequency", "expected_monthly"),
    [(50, "daily", 1500), (300, "weekly", 1299), (200, "monthly", 200)],
)
def test_habit_cost_converts_to_monthly_amount(amount, frequency, expected_monthly):
    # Hand arithmetic: Rs 50 x 30 = Rs 1,500; Rs 300 x 4.33 = Rs 1,299;
    # Rs 200 monthly x 1 = Rs 200.
    result = convert_habit_to_monthly_amount(amount, frequency)
    assert result["raw_monthly_amount"] == pytest.approx(expected_monthly)
    assert result["monthly_amount"] == pytest.approx(expected_monthly)
    assert result["is_capped"] is False


def test_habit_cost_clamps_to_monthly_minimum_and_maximum():
    # Hand arithmetic: Rs 50/month is raised to Rs 100; Rs 200/day x 30 = Rs 6,000,
    # which is capped at Rs 5,000/month.
    below_minimum = convert_habit_to_monthly_amount(50, "monthly")
    above_maximum = convert_habit_to_monthly_amount(200, "daily")
    assert below_minimum["monthly_amount"] == 100
    assert below_minimum["was_raised_to_minimum"] is True
    assert above_maximum["raw_monthly_amount"] == 6000
    assert above_maximum["monthly_amount"] == 5000
    assert above_maximum["is_capped"] is True


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


def test_stress_windows_rank_best_and_worst_with_hand_computable_values():
    # Each window invests Rs 100 on three monthly dates, so total put in is Rs 300.
    # Feb-Apr ends at NAV 80: 3 units x 80 = Rs 240, a Rs 60 / Rs 300 = -20% return.
    # Mar-May buys at NAVs 100, 100, 80: 1 + 1 + 1.25 = 3.25 units.
    # It ends at NAV 120: 3.25 x 120 = Rs 390, a Rs 90 / Rs 300 = +30% return.
    nav_history = [
        {"date": "2024-01-01", "nav": 100},
        {"date": "2024-02-01", "nav": 100},
        {"date": "2024-03-01", "nav": 100},
        {"date": "2024-04-01", "nav": 100},
        {"date": "2024-05-01", "nav": 80},
        {"date": "2024-06-01", "nav": 120},
    ]

    result = stress_test_windows(
        amount=100,
        tenure_months=3,
        nav_history=nav_history,
        selected_window=("2024-01-01", "2024-04-01"),
        instalment_day=1,
    )

    assert result["worst"]["start_date"] == "2024-02-01"
    assert result["worst"]["end_date"] == "2024-05-01"
    assert result["worst"]["total_invested"] == 300
    assert result["worst"]["ending_value"] == pytest.approx(240)
    assert result["worst"]["absolute_return_pct"] == pytest.approx(-20)
    assert result["best"]["start_date"] == "2024-03-01"
    assert result["best"]["end_date"] == "2024-06-01"
    assert result["best"]["total_invested"] == 300
    assert result["best"]["ending_value"] == pytest.approx(390)
    assert result["best"]["absolute_return_pct"] == pytest.approx(30)


def test_stress_test_window_count_matches_start_windows():
    # Six monthly NAV dates with a three-month duration give Jan, Feb, and Mar starts.
    nav_history = [
        {"date": f"2024-{month:02d}-05", "nav": 100}
        for month in range(1, 7)
    ]
    assert stress_test_window_count(nav_history, 3, instalment_day=5) == 3
