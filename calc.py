from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Sequence


def _to_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d").date()
    raise TypeError(f"Unsupported date value: {value!r}")


def _scheduled_monthly_dates(start_date: date, months: int) -> list[date]:
    dates: list[date] = []
    for offset in range(months):
        year = start_date.year + ((start_date.month - 1 + offset) // 12)
        month = (start_date.month - 1 + offset) % 12 + 1
        last_day = monthrange(year, month)[1]
        day = min(start_date.day, last_day)
        dates.append(date(year, month, day))
    return dates


def sip_start_date_for_tenure(
    as_of_date: str | date | datetime,
    tenure_years: int,
    instalment_day: int = 5,
) -> date:
    if tenure_years <= 0:
        raise ValueError("Tenure must be positive.")
    if instalment_day < 1 or instalment_day > 31:
        raise ValueError("Instalment day must be between 1 and 31.")
    as_of = _to_date(as_of_date)
    start_year = as_of.year - tenure_years
    start_day = min(instalment_day, monthrange(start_year, as_of.month)[1])
    return date(start_year, as_of.month, start_day)


def get_tenure_availability(
    nav_history: Sequence[dict],
    as_of_date: str | date | datetime,
    tenure_years: Sequence[int] = (1, 3, 5),
    instalment_day: int = 5,
) -> dict[int, dict]:
    if not nav_history:
        message = "NAV history is empty."
        return {years: {"available": False, "message": message} for years in tenure_years}

    parsed_as_of = _to_date(as_of_date)
    nav_dates = sorted({_to_date(item["date"]) for item in nav_history})
    results = {}
    for years in tenure_years:
        start_date = sip_start_date_for_tenure(parsed_as_of, years, instalment_day)
        scheduled_dates = _scheduled_monthly_dates(start_date, years * 12)
        unavailable_date = next(
            (scheduled for scheduled in scheduled_dates if not any(nav >= scheduled for nav in nav_dates)),
            None,
        )
        if unavailable_date is None:
            results[years] = {
                "available": True,
                "start_date": start_date.isoformat(),
                "message": None,
            }
        else:
            results[years] = {
                "available": False,
                "start_date": start_date.isoformat(),
                "message": (
                    f"Not enough NAV history for {years} years. No NAV date is available on or after "
                    f"{unavailable_date.isoformat()}."
                ),
            }
    return results


def _next_nav_date(scheduled: date, nav_dates: Sequence[date]) -> date:
    for nav_date in nav_dates:
        if nav_date >= scheduled:
            return nav_date
    raise ValueError(f"No NAV date is available on or after {scheduled.isoformat()}.")


def _as_date(value: str | date | datetime | None, fallback: date | None = None) -> date:
    if value is None:
        if fallback is None:
            raise ValueError("A valid date is required.")
        return fallback
    return _to_date(value)


def _xirr_value(cashflows: Sequence[tuple[date, float]], first_date: date) -> float:
    total = 0.0
    for flow_date, amount in cashflows:
        years = (flow_date - first_date).days / 365.0
        total += amount / ((1.0 + 0.0) ** years)
    return total


def xirr(cashflows: Sequence[tuple[str | date | datetime, float]]) -> float:
    """Compute XIRR using a simple bisection solver without external dependencies."""
    if len(cashflows) < 2:
        raise ValueError("At least two cash-flow dates are required for XIRR.")

    normalized = sorted(
        ((_to_date(flow_date), float(amount)) for flow_date, amount in cashflows),
        key=lambda item: item[0],
    )
    first_date = normalized[0][0]
    if normalized[0][1] >= 0:
        raise ValueError("The first cash flow must be negative for an investment-style XIRR.")

    def f(rate: float) -> float:
        total = 0.0
        for flow_date, amount in normalized:
            years = (flow_date - first_date).days / 365.0
            total += amount / ((1.0 + rate) ** years)
        return total

    low = -0.9999
    high = 10.0
    flow_low = f(low)
    flow_high = f(high)

    while flow_low * flow_high > 0 and high < 1_000_000.0:
        high *= 2.0
        flow_high = f(high)

    if flow_low * flow_high > 0:
        raise ValueError("Could not bracket the XIRR root with a valid sign change.")

    for _ in range(500):
        mid = (low + high) / 2.0
        flow_mid = f(mid)
        if abs(flow_mid) < 1e-12:
            return mid
        if flow_low * flow_mid <= 0:
            high = mid
            flow_high = flow_mid
        else:
            low = mid
            flow_low = flow_mid
    return (low + high) / 2.0


def calculate_sip_projection(
    amount: float,
    start_date: str | date | datetime,
    nav_history: Sequence[dict],
    months: int = 12,
    as_of_date: str | date | datetime | None = None,
) -> dict:
    """Project a monthly SIP across historical NAV data.

    Each scheduled contribution is processed on the next available NAV date on or after
    the scheduled date, which mirrors a real SIP on a non-trading day or holiday.
    """
    if amount <= 0:
        raise ValueError("SIP amount must be positive.")
    if months <= 0:
        raise ValueError("Tenure must be positive.")
    if not nav_history:
        raise ValueError("NAV history is empty.")

    parsed_start = _to_date(start_date)
    nav_dates = sorted({_to_date(item["date"]) for item in nav_history})
    nav_by_date = {_to_date(item["date"]): float(item["nav"]) for item in nav_history}
    if not nav_by_date:
        raise ValueError("NAV history is empty.")

    contribution_dates = _scheduled_monthly_dates(parsed_start, months)
    contributions: list[dict] = []
    total_units = 0.0
    total_invested = 0.0

    for scheduled_date in contribution_dates:
        try:
            nav_date = _next_nav_date(scheduled_date, nav_dates)
        except ValueError:
            return {
                "available": False,
                "message": (
                    f"Not enough NAV history to complete the {months}-month simulation. "
                    f"No NAV date is available on or after {scheduled_date.isoformat()}."
                ),
                "required_months": months,
                "available_months": len(contributions),
                "as_of_date": max(nav_dates).isoformat(),
            }
        nav_value = nav_by_date[nav_date]
        units = amount / nav_value
        total_units += units
        total_invested += amount
        contributions.append(
            {
                "date": scheduled_date.isoformat(),
                "nav_date": nav_date.isoformat(),
                "nav": nav_value,
                "amount": amount,
                "units": units,
            }
        )

    if as_of_date is None:
        final_date = max(nav_dates)
    else:
        final_date = _to_date(as_of_date)
        if final_date < min(nav_dates):
            raise ValueError("As-of date is before the available NAV history.")
        final_date = max(d for d in nav_dates if d <= final_date) if any(d <= final_date for d in nav_dates) else max(nav_dates)

    current_value = total_units * nav_by_date[final_date]
    cashflows = [( _to_date(item["nav_date"]), -float(item["amount"])) for item in contributions]
    cashflows.append((final_date, current_value))
    xirr_value = xirr(cashflows)

    portfolio_series = []
    invested_series = []
    units_by_date: dict[date, float] = {}
    invested_by_date: dict[date, float] = {}
    for contribution in contributions:
        contribution_nav_date = _to_date(contribution["nav_date"])
        units_by_date[contribution_nav_date] = units_by_date.get(contribution_nav_date, 0.0) + contribution["units"]
        invested_by_date[contribution_nav_date] = invested_by_date.get(contribution_nav_date, 0.0) + contribution["amount"]

    timeline = []
    units_so_far = 0.0
    invested_so_far = 0.0
    first_contribution_date = _to_date(contributions[0]["nav_date"])
    for nav_date in nav_dates:
        if nav_date < first_contribution_date or nav_date > final_date:
            continue
        units_so_far += units_by_date.get(nav_date, 0.0)
        invested_so_far += invested_by_date.get(nav_date, 0.0)
        portfolio_value = units_so_far * nav_by_date[nav_date]
        timeline.append(
            {
                "date": nav_date.isoformat(),
                "portfolio_value": portfolio_value,
                "invested_so_far": invested_so_far,
            }
        )
        portfolio_series.append(portfolio_value)
        invested_series.append(invested_so_far)

    drawdown = calculate_drawdown_metrics(
        portfolio_series,
        invested_series,
        dates=[item["date"] for item in timeline],
    )

    return {
        "available": True,
        "message": None,
        "start_date": parsed_start.isoformat(),
        "months": months,
        "contributions": contributions,
        "total_invested": total_invested,
        "gain_loss": current_value - total_invested,
        "total_units": total_units,
        "as_of_date": final_date.isoformat(),
        "current_value": current_value,
        "xirr": xirr_value,
        "drawdown": drawdown,
        "timeline": timeline,
        "absolute_return_pct": ((current_value - total_invested) / total_invested) * 100.0,
    }


def calculate_sip_tenure_projection(
    amount: float,
    tenure_years: int,
    nav_history: Sequence[dict],
    as_of_date: str | date | datetime,
    instalment_day: int = 5,
) -> dict:
    start_date = sip_start_date_for_tenure(as_of_date, tenure_years, instalment_day)
    result = calculate_sip_projection(
        amount=amount,
        start_date=start_date,
        nav_history=nav_history,
        months=tenure_years * 12,
        as_of_date=as_of_date,
    )
    result["tenure_years"] = tenure_years
    return result


def calculate_drawdown_metrics(
    portfolio_values: Sequence[float],
    invested_values: Sequence[float],
    dates: Sequence[str | date | datetime] | None = None,
) -> dict:
    """Return both peak-to-trough drawdown and largest portfolio-vs-invested shortfall."""
    if len(portfolio_values) != len(invested_values):
        raise ValueError("portfolio_values and invested_values must be the same length.")
    if dates is not None and len(dates) != len(portfolio_values):
        raise ValueError("dates must have the same length as the value series.")
    if not portfolio_values:
        raise ValueError("At least one value is required for drawdown calculation.")

    parsed_dates = [_to_date(item).isoformat() for item in dates] if dates is not None else None
    peak = portfolio_values[0]
    peak_index = 0
    peak_to_trough_pct = 0.0
    peak_at_max_drawdown = peak
    trough_at_max_drawdown = portfolio_values[0]
    max_drawdown_peak_index = 0
    max_drawdown_trough_index = 0

    for index, value in enumerate(portfolio_values):
        if value > peak:
            peak = value
            peak_index = index
        if peak > 0:
            current_drop = (peak - value) / peak
        else:
            current_drop = 0.0
        if current_drop > peak_to_trough_pct:
            peak_to_trough_pct = current_drop
            peak_at_max_drawdown = peak
            trough_at_max_drawdown = value
            max_drawdown_peak_index = peak_index
            max_drawdown_trough_index = index

    invested_shortfall_pct = 0.0
    invested_shortfall_point = None
    for index, (portfolio_value, invested_total) in enumerate(zip(portfolio_values, invested_values)):
        if invested_total <= 0:
            continue
        shortfall = (invested_total - portfolio_value) / invested_total
        if shortfall > invested_shortfall_pct:
            invested_shortfall_pct = shortfall
            invested_shortfall_point = {
                "portfolio_value": portfolio_value,
                "invested_so_far": invested_total,
                "date": parsed_dates[index] if parsed_dates is not None else None,
            }

    return {
        "peak_to_trough_pct": peak_to_trough_pct,
        "peak_to_trough_value": peak_at_max_drawdown - trough_at_max_drawdown,
        "peak_to_trough_peak_value": peak_at_max_drawdown,
        "peak_to_trough_trough_value": trough_at_max_drawdown,
        "peak_to_trough_peak_date": (
            parsed_dates[max_drawdown_peak_index] if parsed_dates is not None else None
        ),
        "peak_to_trough_trough_date": (
            parsed_dates[max_drawdown_trough_index] if parsed_dates is not None else None
        ),
        "invested_shortfall_pct": invested_shortfall_pct,
        "invested_shortfall_point": invested_shortfall_point,
    }


def stress_test_windows(
    amount: float,
    tenure_months: int,
    nav_history: Sequence[dict],
    selected_window: tuple[str | date | datetime, str | date | datetime],
) -> dict:
    """Slide a window of length tenure_months across the NAV series and rank windows by XIRR."""
    if amount <= 0:
        raise ValueError("Amount must be positive.")
    if tenure_months <= 0:
        raise ValueError("Tenure must be positive.")
    if not nav_history:
        raise ValueError("NAV history is empty.")

    nav_dates = sorted({_to_date(item["date"]) for item in nav_history})
    selected_start = _to_date(selected_window[0])
    selected_end = _to_date(selected_window[1])

    windows: list[dict] = []
    for index, start_date in enumerate(nav_dates):
        if index + tenure_months >= len(nav_dates):
            break
        end_date = nav_dates[index + tenure_months]
        projection = calculate_sip_projection(
            amount=amount,
            start_date=start_date,
            nav_history=nav_history,
            months=tenure_months,
            as_of_date=end_date,
        )
        windows.append(
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "xirr": float(projection["xirr"]),
                "absolute_return_pct": float(projection["absolute_return_pct"]),
            }
        )

    if not windows:
        raise ValueError("No valid tenant windows are available for the chosen history length.")

    ranked = sorted(windows, key=lambda item: item["xirr"])
    selected_projection = calculate_sip_projection(
        amount=amount,
        start_date=selected_start,
        nav_history=nav_history,
        months=tenure_months,
        as_of_date=selected_end,
    )
    selected_result = {
        "start_date": selected_start.isoformat(),
        "end_date": selected_end.isoformat(),
        "xirr": float(selected_projection["xirr"]),
        "absolute_return_pct": float(selected_projection["absolute_return_pct"]),
    }

    return {
        "best": ranked[-1],
        "worst": ranked[0],
        "selected": selected_result,
        "windows": windows,
    }
