from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from cached_data import load_cached_nav_series
from calc import (
	calculate_sip_tenure_projection,
	get_tenure_availability,
)
from data import NavSeriesResult


APP_NAME = "First Step"
FUND_NAME = "Motilal Oswal Nifty 50 Index Fund - Direct Plan - Growth"
TENURE_YEARS = (1, 3, 5)
DEFAULT_AMOUNT = 500

CUSTOM_CSS = """
<style>
[data-testid="stAppViewContainer"] { background: #ffffff; }
[data-testid="stHeader"] { visibility: hidden; height: 0; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 480px; padding: 1.25rem 1rem 1.5rem; }
h1, h2, h3 { color: #15251f; letter-spacing: 0; }
[data-testid="stMetric"] {
  border: 1px solid #e4eee9;
  border-radius: 8px;
  padding: 0.9rem 1rem;
  background: #fbfdfc;
}
[data-testid="stMetricLabel"] { color: #53645d; }
div.stButton > button {
  min-height: 3.1rem;
  border-radius: 8px;
  font-weight: 600;
}
div.stButton > button[kind="primary"] {
  background: #00b386;
  border-color: #00b386;
  color: #ffffff;
}
div.stButton > button[kind="primary"]:hover {
  background: #008f6c;
  border-color: #008f6c;
}
[data-testid="stSlider"] { padding: 0.4rem 0 0.7rem; }
.step-label { color: #008f6c; font-size: 0.82rem; font-weight: 700; }
</style>
"""


def initialize_state() -> None:
	defaults = {
		"screen": 0,
		"amount": DEFAULT_AMOUNT,
		"tenure_years": 3,
		"answer_market": None,
		"answer_money": None,
		"plan_started": False,
	}
	for key, value in defaults.items():
		if key not in st.session_state:
			st.session_state[key] = value


def money(value: float) -> str:
	if value < 0:
		return f"-Rs {abs(value):,.0f}"
	return f"Rs {value:,.0f}"


def day_label(value: str | date) -> str:
	parsed = date.fromisoformat(value) if isinstance(value, str) else value
	return parsed.strftime("%d-%m-%Y")


def nav_history(result: NavSeriesResult) -> list[dict[str, str | float]]:
	return [{"date": nav_date.isoformat(), "nav": nav} for nav_date, nav in result.data]


def render_header(screen: int) -> None:
	st.markdown(f"# {APP_NAME}")
	st.markdown(f'<div class="step-label">STEP {screen + 1} OF 3</div>', unsafe_allow_html=True)


def render_footer(result: NavSeriesResult | None) -> None:
	st.divider()
	if result is None:
		source_text = "NAV data unavailable; as-of date unavailable"
	else:
		source_name = "live" if result.source == "live" else "saved snapshot"
		source_text = f"{source_name}; as of {day_label(result.as_of_date)}"
	st.caption(f"Fund: {FUND_NAME}")
	st.caption(f"Data source: {source_text}")
	st.caption(
		"Assumptions: Rs 500/month by default (Rs 100-Rs 5,000); instalment on the 5th "
		"or next NAV date; 1, 3, or 5 years (3 by default); the window ends on the latest "
		"NAV date in the data, never today's date."
	)
	st.caption(
		"Illustration only, past performance is not a guarantee, this is not investment advice."
	)
	st.caption("Independent case-study prototype, not affiliated with Groww.")


def render_source_banner(result: NavSeriesResult) -> None:
	if result.source == "snapshot":
		st.warning(
			f"Using the saved NAV snapshot. Its latest data is from {day_label(result.as_of_date)}."
		)


def render_start_screen(
	result: NavSeriesResult,
	history: list[dict[str, str | float]],
	availability: dict[int, dict],
) -> None:
	st.title("Start small")
	st.write("A SIP is a fixed amount put in regularly. Here, each payment is simulated.")
	st.slider(
		"Monthly amount",
		min_value=100,
		max_value=5000,
		step=100,
		format="Rs %d",
		key="amount",
	)

	supported = [years for years in TENURE_YEARS if availability[years]["available"]]
	st.markdown("**Time horizon**")
	if not supported:
		st.error("This NAV history cannot support any of the available time horizons.")
	else:
		if st.session_state.tenure_years not in supported:
			st.session_state.tenure_years = 3 if 3 in supported else supported[0]
		st.radio(
			"Choose a time horizon",
			options=supported,
			format_func=lambda years: f"{years} year" if years == 1 else f"{years} years",
			horizontal=True,
			label_visibility="collapsed",
			key="tenure_years",
		)
	for years in TENURE_YEARS:
		if not availability[years]["available"]:
			st.caption(f"{years} years unavailable: {availability[years]['message']}")

	if st.button("See what would have happened", type="primary", use_container_width=True, disabled=not supported):
		st.session_state.screen = 1


def render_projection(result: NavSeriesResult, history: list[dict[str, str | float]]) -> dict | None:
	projection = calculate_sip_tenure_projection(
		amount=float(st.session_state.amount),
		tenure_years=int(st.session_state.tenure_years),
		nav_history=history,
		as_of_date=result.as_of_date,
		instalment_day=5,
	)
	if not projection["available"]:
		st.warning(projection["message"])
		return None
	return projection


def render_drawdowns(projection: dict) -> None:
	metrics = projection["drawdown"]
	st.subheader("Biggest fall")
	st.caption("Drawdown means the biggest fall in the simulated value.")
	peak_date = metrics["peak_to_trough_peak_date"]
	trough_date = metrics["peak_to_trough_trough_date"]
	if peak_date is None or trough_date is None:
		st.write("No drop from a previous high appeared in this simulation.")
	else:
		st.markdown(
			f"The largest drop from a high was **{metrics['peak_to_trough_pct']:.1%}**: "
			f"from {money(metrics['peak_to_trough_peak_value'])} on {day_label(peak_date)} "
			f"to {money(metrics['peak_to_trough_trough_value'])} on {day_label(trough_date)}."
		)

	shortfall = metrics["invested_shortfall_point"]
	if shortfall is None:
		st.write("The simulated value did not fall below the amount put in so far.")
	else:
		st.markdown(
			f"The lowest point against what had been put in so far was **{metrics['invested_shortfall_pct']:.1%} below**: "
			f"{money(shortfall['portfolio_value'])} versus {money(shortfall['invested_so_far'])} "
			f"on {day_label(shortfall['date'])}."
		)


def render_results_screen(
	result: NavSeriesResult,
	history: list[dict[str, str | float]],
) -> dict | None:
	st.title("What would have happened")
	projection = render_projection(result, history)
	if projection is None:
		back, _ = st.columns(2)
		if back.button("Back", use_container_width=True):
			st.session_state.screen = 0
		return None

	first_row = st.columns(2)
	first_row[0].metric("Total put in", money(projection["total_invested"]))
	first_row[1].metric("Value today", money(projection["current_value"]))
	second_row = st.columns(2)
	second_row[0].metric("Gain / loss", money(projection["gain_loss"]))
	second_row[1].metric("Yearly growth rate", f"{projection['xirr']:.1%}")
	st.caption(
		f"Value is based on NAV through {day_label(projection['as_of_date'])}. "
		"NAV (net asset value) is the fund's published price per unit."
	)
	st.caption("Yearly growth rate is also called XIRR; it accounts for when each payment happened.")

	chart_data = pd.DataFrame(projection["timeline"])
	chart_data["date"] = pd.to_datetime(chart_data["date"])
	chart_data = chart_data.set_index("date").rename(
		columns={"portfolio_value": "Simulated value", "invested_so_far": "Amount put in"}
	)
	st.line_chart(chart_data[["Simulated value", "Amount put in"]], height=280)
	render_drawdowns(projection)

	back, next_step = st.columns(2)
	if back.button("Back", use_container_width=True):
		st.session_state.screen = 0
	if next_step.button("Next", type="primary", use_container_width=True):
		st.session_state.screen = 2
	return projection


def render_question(
	prompt: str,
	options: tuple[str, ...],
	key: str,
	correct_answer: str,
	correct_feedback: str,
	incorrect_feedback: str,
) -> bool:
	answer = st.radio(prompt, options, index=None, key=key)
	if answer is None:
		return False
	is_correct = answer == correct_answer
	if is_correct:
		st.success(correct_feedback)
	else:
		st.info(incorrect_feedback)
	return is_correct


def reset_journey() -> None:
	st.session_state.screen = 0
	st.session_state.amount = DEFAULT_AMOUNT
	st.session_state.tenure_years = 3
	st.session_state.answer_market = None
	st.session_state.answer_money = None
	st.session_state.plan_started = False


def render_check_screen(projection: dict | None) -> None:
	st.title("Check and start")
	if st.session_state.plan_started:
		st.success("Your simulated plan is ready.")
		st.metric("Simulated monthly amount", money(float(st.session_state.amount)))
		st.metric("Historical value at the end", money(projection["current_value"]))
		st.caption(
			f"This illustration covers {projection['tenure_years']} years and ends on "
			f"{day_label(projection['as_of_date'])}. No real payment was made."
		)
		if st.button("Start over", type="primary", use_container_width=True):
			reset_journey()
		return

	market_correct = render_question(
		"The market falls 20% a month after you start. What does this tool tell you?",
		(
			"The simulated value can fall; past data cannot tell me what happens next.",
			"The value will return to where it started within a month.",
			"The tool will stop the market from falling further.",
		),
		"answer_market",
		"The simulated value can fall; past data cannot tell me what happens next.",
		"Right. A historical simulation can show a fall, but it cannot predict or prevent one.",
		"Try again. This tool shows one past path; it cannot predict or prevent a future fall.",
	)
	money_correct = render_question(
		"Did any real money move when you tried this plan?",
		(
			"No. The plan and every payment are simulated.",
			"Yes. The first payment was sent to the fund.",
			"Only a small real payment was made for the illustration.",
		),
		"answer_money",
		"No. The plan and every payment are simulated.",
		"Correct. Nothing was bought or paid for in this prototype.",
		"Try again. This prototype does not send payments or place orders.",
	)

	back, start = st.columns(2)
	if back.button("Back", use_container_width=True):
		st.session_state.screen = 1
	if start.button(
		"Start simulated plan",
		type="primary",
		use_container_width=True,
		disabled=not (market_correct and money_correct),
	):
		st.session_state.plan_started = True
		st.rerun()


def main() -> None:
	st.set_page_config(page_title=APP_NAME, layout="centered")
	initialize_state()
	st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

	with st.spinner("Loading fund NAV history..."):
		try:
			result = load_cached_nav_series()
		except (RuntimeError, ValueError, OSError) as exc:
			render_header(0)
			st.error(f"We couldn't load the fund's NAV history. Please try again later. Details: {exc}")
			render_footer(None)
			return

	render_source_banner(result)
	screen = int(st.session_state.screen)
	render_header(screen)
	history = nav_history(result)
	availability = get_tenure_availability(history, result.as_of_date, TENURE_YEARS, instalment_day=5)

	projection = None
	if screen == 0:
		render_start_screen(result, history, availability)
	elif screen == 1:
		projection = render_results_screen(result, history)
	else:
		projection = render_projection(result, history)
		if projection is None:
			st.warning("The selected time horizon is not available with this NAV history.")
			if st.button("Back", use_container_width=True):
				st.session_state.screen = 0
		else:
			render_check_screen(projection)

	render_footer(result)


if __name__ == "__main__":
	main()
