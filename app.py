from __future__ import annotations

from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from cached_data import load_cached_nav_series
from calc import (
	analyze_largest_nav_fall,
	convert_habit_to_monthly_amount,
	calculate_sip_tenure_projection,
	get_tenure_availability,
	sip_start_date_for_tenure,
	stress_test_window_count,
	stress_test_windows,
)
from data import NavSeriesResult


APP_NAME = "First Step"
FUND_NAME = "Motilal Oswal Nifty 50 Index Fund - Direct Plan - Growth"
TENURE_YEARS = (1, 3, 5)
DEFAULT_AMOUNT = 500
AMOUNT_PICKS = (100, 500, 1000, 2500)
HABIT_PRESETS = {
	"Coffee / chai (Rs 50/day, illustrative)": (50.0, "daily"),
	"Snacks (Rs 100/day, illustrative)": (100.0, "daily"),
	"Food delivery (Rs 300/week, illustrative)": (300.0, "weekly"),
	"One subscription (Rs 200/month, illustrative)": (200.0, "monthly"),
	"Your own habit": None,
}
DEFAULT_HABIT = "Coffee / chai (Rs 50/day, illustrative)"


def preset_habit_cost(habit: str) -> tuple[float, str]:
	values = HABIT_PRESETS[habit]
	if values is None:
		raise ValueError("Custom habits do not have preset cost values.")
	return values


DEFAULT_SMALL_MONTHLY_AMOUNT = convert_habit_to_monthly_amount(
	*preset_habit_cost(DEFAULT_HABIT)
)["monthly_amount"]
QUIZ_QUESTIONS = (
	{
		"key": "market",
		"prompt": "The market falls 20% a month later. What does this tool tell you?",
		"options": (
			"Your simulated value can fall. Past data cannot predict what comes next.",
			"Your value will bounce back within a month.",
			"The tool will stop the market from falling.",
		),
		"answer": "Your simulated value can fall. Past data cannot predict what comes next.",
		"feedback": "Exactly. A past path cannot promise what happens next.",
		"retry": "Give it another go. The tool cannot predict or prevent a fall.",
	},
	{
		"key": "money",
		"prompt": "Did any real money move during this example?",
		"options": (
			"No. The plan and every payment are simulated.",
			"Yes. The first payment went to the fund.",
			"A small real payment covered the example.",
		),
		"answer": "No. The plan and every payment are simulated.",
		"feedback": "Right. Nothing was bought or paid for here.",
		"retry": "Try again. This prototype never moves money.",
	},
)


def apply_custom_css() -> None:
	st.markdown(
		"""
		<style>
		[data-testid="stAppViewContainer"] { background: #0E0F11; }
		[data-testid="stHeader"] { visibility: hidden; height: 0; }
		#MainMenu, footer { visibility: hidden; }
		.block-container { max-width: 480px; padding: 1.35rem 1rem 2rem; }
		:root { color-scheme: dark; }
		h1, h2, h3, p, label { letter-spacing: 0 !important; }
		h1 { color: #F3F5F4; font-size: 1.45rem !important; line-height: 1.28; }
		h2, h3 { color: #F3F5F4; }
		[data-testid="stCaptionContainer"] { color: #92999B; }
		[data-testid="stProgressBar"] > div > div > div > div {
			background: #00D09C;
		}
		[data-testid="stProgressBar"] { margin: 0.25rem 0 1.2rem; }
		div.stButton > button {
			min-height: 3.15rem;
			border-radius: 16px;
			border: 1px solid #303437;
			background: #1A1C1F;
			color: #F3F5F4;
			font-weight: 650;
		}
		div.stButton > button:hover { border-color: #00D09C; color: #00D09C; }
		div.stButton > button[kind="primary"] {
			background: #00D09C;
			border-color: #00D09C;
			color: #071510;
		}
		div.stButton > button[kind="primary"]:hover {
			background: #23E2B1;
			border-color: #23E2B1;
			color: #071510;
		}
		[data-testid="stSlider"] [role="slider"] { background: #00D09C; }
		[data-testid="stRadio"] div[role="radiogroup"] { gap: 0.5rem; }
		[data-testid="stRadio"] div[role="radiogroup"] label {
			border: 1px solid #303437;
			border-radius: 999px;
			background: #1A1C1F;
			padding: 0.55rem 0.85rem;
		}
		[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
			border-color: #00D09C;
			background: #10251F;
		}
		.st-key-quick_amount [data-testid="stRadio"] div[role="radiogroup"] { gap: 0.25rem; }
		.st-key-quick_amount [data-testid="stRadio"] div[role="radiogroup"] label {
			padding: 0.4rem 0.5rem;
			white-space: nowrap;
		}
		[data-testid="stExpander"] {
			border: 1px solid #303437;
			border-radius: 16px;
			background: #141618;
		}
		.hero-card, .story-card, .confirmation-card {
			border: 1px solid #303437;
			border-radius: 16px;
			background: #1A1C1F;
			padding: 1.1rem 1.15rem;
			margin: 0.4rem 0 1rem;
		}
		.hero-kicker { color: #A0A8A7; font-size: 0.9rem; }
		.hero-value { color: #F3F5F4; font-size: 2rem; font-weight: 750; line-height: 1.22; }
		.hero-sub { color: #A0A8A7; font-size: 0.92rem; margin-top: 0.45rem; }
		.gain-pill { color: #00D09C; font-size: 0.88rem; font-weight: 700; }
		.loss-pill { color: #FF8B8B; font-size: 0.88rem; font-weight: 700; }
		.story-title { color: #F3F5F4; font-weight: 700; margin-bottom: 0.4rem; }
		.story-copy { color: #CFD4D2; line-height: 1.55; }
		.footer-line { color: #858D8E; font-size: 0.76rem; text-align: center; padding-top: 1rem; }
		@media (max-width: 520px) {
			.block-container { padding: 1rem 0.85rem 1.5rem; }
			.hero-value { font-size: 1.75rem; }
		}
		</style>
		""",
		unsafe_allow_html=True,
	)


def initialize_state() -> None:
	defaults = {
		"screen": 0,
		"view": "home",
		"panic_step": 1,
		"panic_answer": None,
		"small_habit": DEFAULT_HABIT,
		"small_custom_cost": 100.0,
		"small_custom_frequency": "monthly",
		"small_monthly_amount": DEFAULT_SMALL_MONTHLY_AMOUNT,
		"small_change_projection": None,
		"small_change_signature": None,
		"timing_comparison": None,
		"timing_signature": None,
		"amount": DEFAULT_AMOUNT,
		"amount_pick": DEFAULT_AMOUNT,
		"tenure_years": 3,
		"quiz_index": 0,
		"quiz_correct": [False, False],
		"plan_started": False,
	}
	for key, value in defaults.items():
		if key not in st.session_state:
			st.session_state[key] = value


def money(value: float) -> str:
	if value < 0:
		return f"−₹{abs(value):,.0f}"
	return f"₹{value:,.0f}"


def day_label(value: str | date) -> str:
	parsed = date.fromisoformat(value) if isinstance(value, str) else value
	return parsed.strftime("%d %b %Y")


def nav_history(result: NavSeriesResult) -> list[dict[str, str | float]]:
	return [{"date": nav_date.isoformat(), "nav": nav} for nav_date, nav in result.data]


def go_home() -> None:
	st.session_state.view = "home"


def render_header(progress: tuple[int, int] | None = None) -> None:
	brand, home = st.columns([3, 1])
	with brand:
		st.markdown(f"### {APP_NAME}")
	with home:
		if st.session_state.view != "home":
			if st.button("Home", key="home_link", width="stretch"):
				go_home()
				st.rerun()
	if progress is not None:
		current, total = progress
		st.progress(current / total, text=f"Step {current} of {total}")


def render_about_data(result: NavSeriesResult | None) -> None:
	with st.expander("About this data"):
		st.caption(f"Fund: {FUND_NAME}")
		if result is None:
			st.caption("NAV source and as-of date are unavailable.")
		else:
			source = "live mfapi.in data" if result.source == "live" else "saved snapshot"
			st.caption(f"Source: {source}. Latest NAV: {day_label(result.as_of_date)}.")
		st.caption(
			"Assumptions: Rs 500/month by default, from Rs 100 to Rs 5,000. "
			"Payments are scheduled on the 5th or next NAV date. "
			"Choose 1, 3, or 5 years. SIP examples end on the latest NAV date, never today. "
			"The panic example models Rs 10,000 at a historical peak. Daily costs use 30 days; weekly costs use 4.33 weeks."
		)
		st.caption("Past performance is not a guarantee. This is not investment advice.")


def render_footer(result: NavSeriesResult | None) -> None:
	st.markdown(
		'<div class="footer-line">Illustration using real past data. Not advice. Not affiliated with Groww.</div>',
		unsafe_allow_html=True,
	)
	render_about_data(result)


def render_source_banner(result: NavSeriesResult) -> None:
	if result.source == "snapshot":
		st.warning(f"Using saved data, last updated {day_label(result.as_of_date)}.")


def open_view(view: str) -> None:
	st.session_state.view = view
	if view == "panic":
		st.session_state.panic_step = 1
		st.session_state.panic_answer = None
		st.session_state.pop("panic_answer_widget", None)


def render_home() -> None:
	st.title("Confidence before commitment")
	st.caption("Three ways to explore the worry behind starting.")

	with st.container(border=True):
		st.subheader("Start small")
		st.caption("See one small monthly plan against real past data.")
		if st.button("Open Start small", key="home_start_small", type="primary", width="stretch"):
			st.session_state.view = "sip"
			st.session_state.screen = 0
			st.rerun()

	with st.container(border=True):
		st.subheader("Would you have panicked?")
		st.caption("Explore one of the fund's biggest past falls.")
		if st.button("Open the panic lens", key="home_panic", width="stretch"):
			open_view("panic")
			st.rerun()

	with st.container(border=True):
		st.subheader("Small change")
		st.caption("Imagine what a small monthly amount might have done.")
		if st.button("Open Small change", key="home_small_change", width="stretch"):
			open_view("small_change")
			st.rerun()

	with st.container(border=True):
		st.subheader("Bad timing test")
		st.caption("Compare different historical start dates.")
		if st.button("Open Bad timing test", key="home_bad_timing", width="stretch"):
			open_view("bad_timing")
			st.rerun()


def panic_chart(fall: dict) -> None:
	chart_data = pd.DataFrame(fall["history"])
	chart_data["date"] = pd.to_datetime(chart_data["date"])
	chart = (
		alt.Chart(chart_data)
		.mark_line(color="#00D09C", strokeWidth=3, point=True)
		.encode(
			x=alt.X("date:T", title=None, axis=alt.Axis(grid=False, labelColor="#91999A")),
			y=alt.Y("value:Q", title="Simulated value (Rs)", axis=alt.Axis(grid=False, labelColor="#91999A")),
			tooltip=[alt.Tooltip("date:T", title="Date"), alt.Tooltip("value:Q", title="Value", format=",.0f")],
		)
		.properties(
			height=220,
			background="#0E0F11",
			padding={"left": 4, "right": 4, "top": 4, "bottom": 4},
		)
		.configure_view(strokeOpacity=0)
		.configure_axis(domainColor="#303437", tickSize=3, titleColor="#92999B", titleFontSize=11)
	)
	st.altair_chart(chart, width="stretch")


def render_panic_step_one(fall: dict) -> None:
	st.title("Would you have panicked?")
	st.markdown(f"Imagine you put in **Rs 10,000** on {day_label(fall['peak_date'])}.")
	panic_chart(fall)
	st.metric("At the lowest point", money(fall["trough_value"]))
	answer = st.radio(
		"Would you sell here?",
		options=("Sell", "Hold", "Not sure"),
		index=None,
		key="panic_answer_widget",
		horizontal=True,
	)
	if answer is not None:
		st.session_state.panic_answer = answer
	if st.button(
		"See what happened next",
		type="primary",
		width="stretch",
		disabled=answer is None,
	):
		st.session_state.panic_step = 2
		st.rerun()


def render_panic_step_two(fall: dict) -> None:
	st.title("What happened next")
	st.markdown("Here is how this past stretch unfolded.")
	st.markdown(
		f'<div class="hero-card"><div class="hero-kicker">Rs 10,000 at the peak became</div>'
		f'<div class="hero-value">{money(fall["latest_value"])}</div>'
		f'<div class="hero-sub">by {day_label(fall["latest_date"])}</div></div>',
		unsafe_allow_html=True,
	)
	if fall["recovery_date"] is None:
		st.markdown(
			'<div class="story-card"><div class="story-title">Getting back to the start</div>'
			'<div class="story-copy">The NAV did not reach its earlier high again within this data.</div></div>',
			unsafe_allow_html=True,
		)
	else:
		st.markdown(
			f'<div class="story-card"><div class="story-title">Getting back to the start</div>'
			f'<div class="story-copy">It took {fall["recovery_days"]:,} days to reach the starting value again, '
			f"on {day_label(fall['recovery_date'])}.</div></div>",
			unsafe_allow_html=True,
		)
	st.caption(
		"This is one fall in one stretch of data (since Dec 2019). "
		"Not every fall recovers this fast, and past results don't predict the future."
	)
	if st.button("Back to home", type="primary", width="stretch"):
		go_home()
		st.rerun()


def render_panic_lens(history: list[dict[str, str | float]]) -> None:
	fall = analyze_largest_nav_fall(history)
	step = int(st.session_state.panic_step)
	if step == 1:
		render_header((1, 2))
		render_panic_step_one(fall)
	else:
		render_header((2, 2))
		render_panic_step_two(fall)


def render_small_change(
	result: NavSeriesResult,
	history: list[dict[str, str | float]],
	availability: dict[int, dict],
) -> None:
	st.title("Small change")
	st.caption("What if just a part of a habit became a monthly SIP?")
	st.selectbox(
		"Pick a habit",
		options=tuple(HABIT_PRESETS),
		key="small_habit",
		on_change=sync_small_change_amount,
	)

	if st.session_state.small_habit == "Your own habit":
		st.number_input(
			"Your habit cost",
			min_value=0.0,
			max_value=100_000.0,
			step=10.0,
			key="small_custom_cost",
			on_change=sync_small_change_amount,
		)
		st.selectbox(
			"How often?",
			options=("daily", "weekly", "monthly"),
			key="small_custom_frequency",
			on_change=sync_small_change_amount,
		)
	else:
		habit_amount, frequency = HABIT_PRESETS[st.session_state.small_habit]
		frequency_label = {"daily": "day", "weekly": "week", "monthly": "month"}[frequency]
		st.caption(f"Illustrative: Rs {habit_amount:g} per {frequency_label}.")

	conversion = current_habit_conversion()
	st.number_input(
		"Monthly amount to explore",
		min_value=100,
		max_value=5000,
		step=100,
		key="small_monthly_amount",
		help="Edit this amount. Monthly equivalent is capped from Rs 100 to Rs 5,000.",
	)
	st.caption("Daily x 30. Weekly x 4.33. Then the monthly amount is capped at Rs 5,000.")
	if conversion["is_capped"]:
		st.info(f"That habit works out to Rs {conversion['raw_monthly_amount']:,.0f}/month, above the Rs 5,000 cap. Explore a smaller part.")
	elif conversion["was_raised_to_minimum"]:
		st.info("The monthly equivalent is below Rs 100, so the minimum shown is Rs 100.")

	supported = [years for years in TENURE_YEARS if availability[years]["available"]]
	if supported:
		if st.session_state.tenure_years not in supported:
			st.session_state.tenure_years = 3 if 3 in supported else supported[0]
		st.radio(
			"Time horizon",
			options=supported,
			format_func=lambda years: f"{years} year" if years == 1 else f"{years} years",
			horizontal=True,
			key="tenure_years",
		)
	for years in TENURE_YEARS:
		if not availability[years]["available"]:
			st.caption(f"{years} years unavailable: {availability[years]['message']}")

	amount = float(st.session_state.small_monthly_amount)
	tenure = int(st.session_state.tenure_years)
	signature = (amount, tenure)
	if st.button(
		"See this what-if",
		type="primary",
		width="stretch",
		disabled=not supported,
	):
		st.session_state.small_change_projection = calculate_sip_tenure_projection(
			amount=amount,
			tenure_years=tenure,
			nav_history=history,
			as_of_date=result.as_of_date,
			instalment_day=5,
		)
		st.session_state.small_change_signature = signature

	projection = st.session_state.small_change_projection
	if projection is not None and st.session_state.small_change_signature == signature:
		if not projection["available"]:
			st.info(projection["message"])
		else:
			st.markdown(
				f'<div class="hero-card"><div class="hero-kicker">If this money had gone into a SIP</div>'
				f'<div class="hero-value">{money(projection["current_value"])}</div>'
				f'<div class="hero-sub">You\'d have put in {money(projection["total_invested"])} '
				f"by {day_label(projection['as_of_date'])}.</div></div>",
				unsafe_allow_html=True,
			)
			render_chart(projection)
			with st.expander("More details"):
				st.write(f"Yearly growth: {projection['xirr']:.1%}")
				st.caption("Yearly growth accounts for when each simulated payment happened.")
				st.write(f"Biggest dip: {projection['drawdown']['peak_to_trough_pct']:.1%} from a previous high.")


def render_timing_row(label: str, window: dict) -> None:
	with st.container(border=True):
		st.markdown(f"**{label}**")
		st.caption(f"{day_label(window['start_date'])} to {day_label(window['end_date'])}")
		st.write(
			f"Put in {money(window['total_invested'])} · ended at {money(window['ending_value'])} "
			f"· {window['absolute_return_pct']:+.1f}%"
		)


def render_bad_timing(
	result: NavSeriesResult,
	history: list[dict[str, str | float]],
	availability: dict[int, dict],
) -> None:
	st.title("Bad timing test")
	st.caption("Same fund. Same monthly amount. Different start dates.")
	st.caption("Based on data since Dec 2019 (about 6.8 years); few start dates for long tenures.")
	
	st.slider(
		"Monthly amount",
		min_value=100,
		max_value=5000,
		step=100,
		format="Rs %d",
		key="amount",
	)
	supported = [years for years in TENURE_YEARS if availability[years]["available"]]
	if st.session_state.tenure_years not in supported and supported:
		st.session_state.tenure_years = 3 if 3 in supported else supported[0]
	if supported:
		st.radio(
			"Time horizon",
			options=supported,
			format_func=lambda years: f"{years} year" if years == 1 else f"{years} years",
			horizontal=True,
			key="tenure_years",
		)
	for years in TENURE_YEARS:
		if not availability[years]["available"]:
			st.caption(f"{years} years unavailable: {availability[years]['message']}")

	tenure_months = int(st.session_state.tenure_years) * 12
	window_count = stress_test_window_count(history, tenure_months)
	if window_count < 12:
		st.info(
			f"There are only {window_count} possible start windows for this horizon. "
			"That is too few for a useful comparison. Try a shorter horizon."
		)
		st.button("Compare start dates", type="primary", width="stretch", disabled=True)
		return

	if st.button("Compare start dates", type="primary", width="stretch"):
		selected_start = sip_start_date_for_tenure(result.as_of_date, int(st.session_state.tenure_years), 5)
		try:
			st.session_state.timing_comparison = stress_test_windows(
				amount=float(st.session_state.amount),
				tenure_months=tenure_months,
				nav_history=history,
				selected_window=(selected_start, result.as_of_date),
			)
			st.session_state.timing_signature = (float(st.session_state.amount), tenure_months)
			st.rerun()
		except ValueError as exc:
			st.warning(f"We couldn't compare those windows: {exc}")

	signature = (float(st.session_state.amount), tenure_months)
	comparison = st.session_state.timing_comparison
	if comparison is not None and st.session_state.timing_signature == signature:
		render_timing_row("Your selected start", comparison["selected"])
		render_timing_row("Worst start window", comparison["worst"])
		render_timing_row("Best start window", comparison["best"])


def current_habit_conversion() -> dict:
	if st.session_state.small_habit == "Your own habit":
		amount = float(st.session_state.small_custom_cost)
		frequency = str(st.session_state.small_custom_frequency)
	else:
		amount, frequency = preset_habit_cost(st.session_state.small_habit)
	return convert_habit_to_monthly_amount(amount, frequency)


def sync_small_change_amount() -> None:
	conversion = current_habit_conversion()
	st.session_state.small_monthly_amount = conversion["monthly_amount"]


def set_amount_from_pick() -> None:
	amount_pick = st.session_state.amount_pick
	if amount_pick is not None:
		st.session_state.amount = amount_pick


def set_pick_from_amount() -> None:
	amount = st.session_state.amount
	st.session_state.amount_pick = amount if amount in AMOUNT_PICKS else None


def render_start_screen(availability: dict[int, dict]) -> None:
	st.title(f"What if you started with just {money(st.session_state.amount)} a month?")
	st.caption("Pick an amount that feels small enough to explore.")

	with st.container(key="quick_amount"):
		st.radio(
			"Quick amount",
			options=AMOUNT_PICKS,
			format_func=lambda amount: f"₹{amount:,}",
			horizontal=True,
			label_visibility="collapsed",
			key="amount_pick",
			on_change=set_amount_from_pick,
		)
	st.slider(
		"Fine-tune your monthly amount",
		min_value=100,
		max_value=5000,
		step=100,
		format="₹%d",
		key="amount",
		on_change=set_pick_from_amount,
	)

	supported = [years for years in TENURE_YEARS if availability[years]["available"]]
	if st.session_state.tenure_years not in supported and supported:
		st.session_state.tenure_years = 3 if 3 in supported else supported[0]
	if supported:
		st.radio(
			"How long?",
			options=supported,
			format_func=lambda years: f"{years} year" if years == 1 else f"{years} years",
			horizontal=True,
			key="tenure_years",
		)
	for years in TENURE_YEARS:
		if not availability[years]["available"]:
			st.caption(f"{years} years unavailable: {availability[years]['message']}")
	if not supported:
		st.error("This history cannot support the listed time horizons.")

	with st.expander("What is a SIP?"):
		st.write("A SIP is a set amount added regularly. This example only simulates those payments.")
	if st.button(
		"See what would have happened",
		type="primary",
		width="stretch",
		disabled=not supported,
	):
		st.session_state.screen = 1
		st.rerun()


def calculate_projection(result: NavSeriesResult, history: list[dict[str, str | float]]) -> dict | None:
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


def render_hero(projection: dict) -> None:
	amount_put_in = money(projection["total_invested"])
	value_now = money(projection["current_value"])
	change = projection["gain_loss"]
	pill_class = "gain-pill" if change >= 0 else "loss-pill"
	change_text = f"{money(abs(change))} {'up' if change >= 0 else 'down'}"
	st.markdown(
		f'<div class="hero-card"><div class="hero-kicker">If you had put in {amount_put_in} '
		f"over {projection['tenure_years']} years</div><div class=\"hero-value\">{value_now}</div>"
		f'<div class="hero-sub">as of {day_label(projection["as_of_date"])} '
		f'<span class="{pill_class}">{change_text}</span></div></div>',
		unsafe_allow_html=True,
	)


def render_chart(projection: dict) -> None:
	chart_data = pd.DataFrame(projection["timeline"])
	chart_data["date"] = pd.to_datetime(chart_data["date"])
	chart_data = chart_data.melt(
		id_vars="date",
		value_vars=["portfolio_value", "invested_so_far"],
		var_name="series",
		value_name="value",
	)
	chart_data["series"] = chart_data["series"].map(
		{"portfolio_value": "Portfolio value", "invested_so_far": "Money put in"}
	)
	chart = (
		alt.Chart(chart_data)
		.mark_line(strokeWidth=2.5, interpolate="monotone")
		.encode(
			x=alt.X("date:T", title=None, axis=alt.Axis(grid=False, labelColor="#91999A", tickColor="#303437")),
			y=alt.Y("value:Q", title="Rupees", axis=alt.Axis(grid=False, labelColor="#91999A", tickColor="#303437")),
			color=alt.Color(
				"series:N",
				legend=alt.Legend(title=None, orient="top", labelColor="#C4CAC8"),
				scale=alt.Scale(
					domain=["Portfolio value", "Money put in"],
					range=["#00D09C", "#747C7E"],
				),
			),
			tooltip=[
				alt.Tooltip("date:T", title="Date"),
				alt.Tooltip("series:N", title="Line"),
				alt.Tooltip("value:Q", title="Rupees", format=",.0f"),
			],
		)
		.properties(height=230, background="#0E0F11", padding={"left": 4, "right": 4, "top": 6, "bottom": 4})
		.configure_view(strokeOpacity=0)
		.configure_axis(domainColor="#303437", tickSize=3, titleColor="#92999B", titleFontSize=11)
		.configure_legend(symbolStrokeWidth=3)
	)
	st.altair_chart(chart, width="stretch")


def render_biggest_dip(projection: dict) -> None:
	metrics = projection["drawdown"]
	peak_date = metrics["peak_to_trough_peak_date"]
	trough_date = metrics["peak_to_trough_trough_date"]
	if peak_date is None or trough_date is None:
		story = "This path had no dip from an earlier high."
	else:
		peak_month = date.fromisoformat(peak_date).strftime("%B %Y")
		trough_month = date.fromisoformat(trough_date).strftime("%B %Y")
		story = (
			f"It fell {metrics['peak_to_trough_pct']:.1%} from {money(metrics['peak_to_trough_peak_value'])} "
			f"in {peak_month} to {money(metrics['peak_to_trough_trough_value'])} in {trough_month}."
		)
	st.markdown(
		f'<div class="story-card"><div class="story-title">Biggest dip</div>'
		f'<div class="story-copy">{story}</div></div>',
		unsafe_allow_html=True,
	)


def render_more_details(projection: dict) -> None:
	with st.expander("More details"):
		st.write(f"Yearly growth: {projection['xirr']:.1%}")
		st.caption("Yearly growth accounts for when each simulated payment happened.")
		metrics = projection["drawdown"]
		shortfall = metrics["invested_shortfall_point"]
		if shortfall is None:
			st.write("Lowest point versus money put in: no shortfall in this path.")
		else:
			st.write(
				f"Lowest point versus money put in: {metrics['invested_shortfall_pct']:.1%} below, "
				f"{money(shortfall['portfolio_value'])} versus {money(shortfall['invested_so_far'])} "
				f"on {day_label(shortfall['date'])}."
			)
		st.write("Scheduled and matched payment dates")
		st.dataframe(
			pd.DataFrame(
				[
					{
						"Scheduled": day_label(item["date"]),
						"NAV date": day_label(item["nav_date"]),
						"Units": f"{item['units']:.4f}",
					}
					for item in projection["contributions"]
				]
			),
			width="stretch",
			hide_index=True,
		)


def render_results_screen(projection: dict | None) -> None:
	st.title("What would have happened")
	if projection is None:
		st.warning("This time span does not fit the available data.")
		if st.button("Back", width="stretch"):
			st.session_state.screen = 0
			st.rerun()
		return

	render_hero(projection)
	render_chart(projection)
	render_biggest_dip(projection)
	render_more_details(projection)
	back, next_step = st.columns(2)
	if back.button("Back", width="stretch"):
		st.session_state.screen = 0
		st.rerun()
	if next_step.button("Next", type="primary", width="stretch"):
		st.session_state.screen = 2
		st.rerun()


def render_question() -> None:
	question_index = st.session_state.quiz_index
	question = QUIZ_QUESTIONS[question_index]
	st.title("Check and start")
	st.caption(f"Question {question_index + 1} of 2")
	st.subheader(question["prompt"])
	answer = st.radio(
		"Choose one",
		options=question["options"],
		index=None,
		key=f"answer_{question['key']}_{question_index}",
		label_visibility="collapsed",
	)
	correct = answer == question["answer"]
	if answer is not None:
		if correct:
			st.success(question["feedback"])
		else:
			st.info(question["retry"])
	
	if correct:
		st.session_state.quiz_correct[question_index] = True
		button_label = "Start simulated plan" if question_index == 1 else "Next question"
		if st.button(button_label, type="primary", width="stretch"):
			if question_index == 1:
				st.session_state.plan_started = True
			else:
				st.session_state.quiz_index = 1
			st.rerun()
	if st.button("Back", width="stretch"):
		st.session_state.screen = 1
		st.rerun()


def reset_journey() -> None:
	for key in ("answer_market_0", "answer_money_1"):
		st.session_state.pop(key, None)
	st.session_state.screen = 0
	st.session_state.amount = DEFAULT_AMOUNT
	st.session_state.amount_pick = DEFAULT_AMOUNT
	st.session_state.tenure_years = 3
	st.session_state.quiz_index = 0
	st.session_state.quiz_correct = [False, False]
	st.session_state.plan_started = False
	st.rerun()


def render_confirmation(projection: dict) -> None:
	st.title("Check and start")
	st.markdown(
		'<div class="confirmation-card"><div class="story-title">All set ✨</div>'
		'<div class="story-copy">Simulated plan started. No real money moved.</div></div>',
		unsafe_allow_html=True,
	)
	st.caption(
		f"{money(float(st.session_state.amount))} each month for "
		f"{projection['tenure_years']} years. Just an illustration."
	)
	if st.button("Start over", type="primary", width="stretch"):
		reset_journey()


def main() -> None:
	st.set_page_config(page_title=APP_NAME, layout="centered")
	initialize_state()
	apply_custom_css()

	with st.spinner("Loading fund history..."):
		try:
			result = load_cached_nav_series()
		except (RuntimeError, ValueError, OSError) as exc:
			render_header()
			st.error(f"We couldn't load the fund history. Please try again later. Details: {exc}")
			render_footer(None)
			return

	render_source_banner(result)
	history = nav_history(result)
	view = st.session_state.view
	if view == "home":
		render_header()
		render_home()
	elif view == "sip":
		screen = int(st.session_state.screen)
		render_header((screen + 1, 3))
		availability = get_tenure_availability(history, result.as_of_date, TENURE_YEARS, instalment_day=5)
		if screen == 0:
			render_start_screen(availability)
		elif screen == 1:
			projection = calculate_projection(result, history)
			render_results_screen(projection)
		elif st.session_state.plan_started:
			projection = calculate_projection(result, history)
			render_confirmation(projection)
		else:
			render_question()
	elif view == "panic":
		render_panic_lens(history)
	else:
		render_header()
		availability = get_tenure_availability(history, result.as_of_date, TENURE_YEARS, instalment_day=5)
		if view == "small_change":
			render_small_change(result, history, availability)
		else:
			render_bad_timing(result, history, availability)
	render_footer(result)


if __name__ == "__main__":
	main()