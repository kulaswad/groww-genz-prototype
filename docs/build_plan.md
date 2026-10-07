# Groww Gen Z prototype plan — revised, depth-expanded, still 1 journey / 3 screens

## Objective

Build a small, mobile-first, educational prototype that helps a first-time salaried investor understand a recurring SIP decision without implying that it is financial advice or a real investment. The product should test whether clearer language and transparent historical context improve confidence.

The prototype remains a single journey with a hard maximum of three screens:
1. Start small
2. What would have happened
3. Check and start

Everything else is optional and can be cut without breaking the core story.

## Product boundaries and scope

### In scope
- One user journey for a first-job salaried beginner
- One mutual fund only, selected after verifying the exact scheme code in mfapi.in
- Monthly SIP default of ₹500; user-editable range ₹100–₹5,000
- Tenure choices: 1, 3, 5 years
- Real NAV-history backtest
- Plain-language explanation of risk and drawdown
- Clear labels: illustration, not advice; historical performance is not a guarantee
- Short comprehension check before simulated start
- Visible data source, as-of date, and disclaimer on every screen
- Optional depth additions clearly marked as optional

### Out of scope
- Multi-fund browsing
- AI recommendations
- Social features or gamification
- Real brokerage, KYC, payments, or execution
- Withdrawal or pause workflows as a real product claim
- Account aggregation or live portfolio imports
- Multiple asset classes or broader investing learning modules

## Core journey, still max 3 screens

### Screen 1 — Start small
Purpose:
- Choose a realistic small SIP amount and tenure
- Keep the entry point low pressure and easy to understand

Widgets:
- Amount input with default ₹500, min ₹100, max ₹5,000
- Tenure chips: 1, 3, 5 years
- Optional “What can I afford?” panel
- Short explainer copy: “This is just an illustration. It does not mean you should buy or sell.”

Optional addition 1:
- “What can I afford?”:
  - Input: monthly take-home income
  - Input: monthly essentials
  - Compute comfortable SIP range as illustrative only:
    - comfort_floor = max(0, take_home - essentials) × 0.05
    - comfort_ceiling = max(0, take_home - essentials) × 0.15
  - Show as a band: “Illustrative comfort range: ₹X to ₹Y”
  - Label clearly as illustrative, not advice, not a recommendation
  - When user amount is outside range, show a soft nudge: “This is still possible, but it may be a bigger stretch than your current comfort range.”

### Screen 2 — What would have happened
Purpose:
- Show the historical SIP result and plain-language risk context
- Add optional stress test and “life happens” controls

Default content:
- Total invested
- Current value
- XIRR
- Worst dip (largest peak-to-trough fall in portfolio value)
- Simple chart of portfolio value over time
- Source and as-of date
- Historical data label: “Illustration only. Past performance is not a guarantee.”

Optional addition 2: Start-date stress test
- Compare the same SIP for:
  a) user-selected window
  b) worst start date in the same tenure
  c) best start date in the same tenure
- Show invested vs current value for each scenario
- Show worst dip for each scenario
- Define “best” and “worst” precisely:
  - For a chosen amount, tenure, and as-of date, compute final XIRR for each valid start date window
  - Worst = lowest final XIRR
  - Best = highest final XIRR
  - Keep amount and tenure constant across scenarios
  - The user-selected window remains the baseline
- Efficient computation:
  - For a fixed annualized tenure and amount, iterate valid start indices across the history
  - Reuse the same NAV series and the same monthly schedule logic
  - Complexity is roughly O(H × M), where H is total valid historical start points and M is number of contribution months in tenure
  - This is small enough for a single Streamlit app on public NAV history

Optional addition 3: “Life happens” toggle
- Toggle: skip 1–3 months or stop early
- Recompute:
  - skip_n_months: reduce contribution count and update total invested
  - stop_early_after_m_months: stop making contributions after month m and keep the rest of the series as an existing portfolio value
- Label as:
  - “Illustration of flexibility only. This does not describe Groww’s real pause or withdrawal rules.”

### Screen 3 — Check and start
Purpose:
- Confirm the user has understood key limits
- Simulated confirmation only

Widgets:
- 2 short comprehension questions before the simulated start
- Example questions:
  - “This is a historical example only. Does it promise future returns?”
  - “Does this prototype move real money?”
- Confirmation summary:
  - “Simulated plan only”
  - “No real money moves”
  - “This is not an investment recommendation”
- Optional one-line reminder:
  - “Typical redemption time is fund-specific and varies; this is illustrative only, not a promise.”
  - If reviewer risk is high, remove this line entirely

## Calculation spec

### 1) Date handling and parsing
- Use mfapi.in format explicitly: YYYY-MM-DD
- Parse with:
  - datetime.strptime(value, "%Y-%m-%d")
- If parse fails, raise a clear error like:
  - “Data error: NAV date '2026/03/01' does not match required format YYYY-MM-DD”
- This prevents silent day/month swaps or corrupted numbers

### 2) SIP schedule
Given:
- monthly contribution amount A
- contribution start date S
- each month i contributes amount A on the day-of-month equal to the user’s chosen monthly schedule
- if that date is not a valid trading day:
  - use the last NAV date on or before that contribution date
- For a user-selected monthly schedule:
  - contribution dates are generated on each month’s same day-of-month
  - if that day does not exist in a given month, use the last valid day of that month
  - if the resulting date is not a trading day, roll backward to the last valid NAV date

Formula:
- For each contribution month i:
  - contribution_date_i = scheduled date for month i
  - effective_nav_date_i = max{d in NAV dates | d <= contribution_date_i}
  - units_i = A / NAV[effective_nav_date_i]
  - total_units = Σ units_i
  - total_invested = Σ A

### 3) Current value
At as-of date T:
- current_value = total_units × NAV[T]
- where T is the most recent NAV date on or before the application’s as-of stamp

### 4) XIRR
Cash flow series:
- At each contribution date t_i: -A
- At final as-of date T: +current_value
- Solve for r in:
  - 0 = Σ [CF_i / (1 + r)^(days_between(t_i, T) / 365.0)]
- Use a standard numeric root solve (e.g., scipy optimize brentq or any stable IRR implementation)
- For a valid SIP with contributions and final value, XIRR is the annualized effective return

### 5) Drawdown definition
When contributions are arriving, drawdown must be measured on total portfolio value, not invested value.

Define:
- V(t) = portfolio value at time t
- peak_value(t) = max_{s ≤ t} V(s)
- drawdown(t) = (peak_value(t) - V(t)) / peak_value(t)
- worst_drawdown = max_t drawdown(t)

This means:
- if contributions are still coming in, the portfolio may be temporarily below cash invested and still not be “the worst” if the eventual peak was higher
- show as:
  - “Your portfolio value fell by X% from its highest point before recovering”

### 6) Worked examples

Example A — Basic SIP
- Amount: ₹500
- NAV dates: 01-Jan, 01-Feb, 01-Mar
- NAVs: ₹100, ₹110, ₹120
- Contributions on the 1st of each month
- Units:
  - Jan: 500 / 100 = 5
  - Feb: 500 / 110 = 4.545
  - Mar: 500 / 120 = 4.167
- Total units = 13.712
- Total invested = ₹1,500
- If as-of date is 01-Apr and NAV = ₹130:
  - current_value = 13.712 × 130 = ₹1,782.56
- Gain = ₹282.56
- XIRR is roughly the annualized rate implied by the cash-flow series

Example B — Non-trading-day rule
- Contribution date scheduled: 2024-02-29
- 2024-02-29 is not a trading day
- NAV dates: 2024-02-28 = ₹100, 2024-03-01 = ₹102
- Use last valid NAV date on or before the contribution date:
  - effective_nav_date = 2024-02-28
  - units_i = A / 100
- Do not silently jump to 2024-03-01

Example C — Drawdown with contributions
- Month 1 value after contribution = ₹1,000
- Month 2 peak value = ₹1,080
- Month 3 value falls to ₹920
- Drawdown = (1,080 - 920) / 1,080 = 14.81%
- Show this as a portfolio-value drawdown, not “money lost relative to invested”

Example D — Life happens
- User skips 2 months in a 12-month SIP
- Contribution schedule reduces to 10 months
- New total invested = 10 × A
- Recompute units, current value, XIRR, and drawdown using the adjusted cash-flow series

Example E — Start-date stress test
- Same amount and tenure, same as-of date
- Compare start dates:
  - selected start = 2021-01
  - worst start = 2020-11 (lowest XIRR)
  - best start = 2019-06 (highest XIRR)
- Compute final portfolio value and XIRR for each; show a small comparison table

## Data layer plan

### Source and parsing
- Live source: mfapi.in search endpoint and scheme metadata
- Verified format: dates returned as YYYY-MM-DD
- Parse using:
  - datetime.strptime(date_text, "%Y-%m-%d")
- Fail loudly if format mismatches:
  - raise ValueError("NAV date format must be YYYY-MM-DD")
- Add test:
  - parse_date("2024-03-01") returns datetime(2024, 3, 1)
  - parse_date("03-01-2024") raises ValueError

### Caching and fallback
- Cache live fetch with st.cache_data
- Commit a fallback snapshot to:
  - data/nav_snapshot.json
- If live data fails:
  - show a visible error banner
  - show last successful snapshot timestamp
  - show “Using saved snapshot due to live data issue”
  - continue with the fallback dataset
- If both live and fallback fail:
  - show a graceful empty/error state with:
    - “We could not load the historical data right now”
    - “Please try again shortly”
    - no misleading numbers

### Refresh process
- Manual refresh:
  1. fetch latest mfapi.in data
  2. validate date format and required keys
  3. save a new snapshot only after successful parse
  4. update stale-cache message
- Keep full history small enough for a repo snapshot and quick load

## File structure
- app.py
- calc.py
- data.py
- data/nav_snapshot.json
- tests/
  - test_calc.py
  - test_data_parsing.py
  - manual_ux_script.md
- requirements.txt
- `README.md`

## Screen states to design
- Loading state: show data source and spinner
- Error state: fail gracefully with a single retry path
- Empty state: no data available
- Invalid amount or tenure: inline validation
- Tenure longer than history: show “This duration is longer than the available history; we’ll show the max available window”
- Stress test no valid windows: show message and disable comparison chart

## Build sequence (target ~7 hours total)

1. Lock data source and exact fund verification — 30 min
2. Define equations and hand-checkable examples — 45 min
3. Build calc module with formulas and tests — 90 min
4. Build data layer, parser, cache, and fallback — 60 min
5. Build Screen 1 + optional affordability panel — 45 min
6. Build Screen 2 + base backtest + chart — 75 min
7. Add optional stress test and “life happens” toggles — 60 min
8. Build Screen 3 + comprehension checks + disclaimers — 45 min
9. Add edge-case states, polish, mobile review — 45 min
10. Manual UX test pass and final tuning — 45 min

If time is short, cut in this order:
1. Optional “What can I afford?” panel
2. Stress test
3. “Life happens” toggle
4. redemption line in Screen 3

## Test plan

### Unit tests
- parse_date returns correct datetime for YYYY-MM-DD
- parse_date rejects wrong format
- SIP contributions generate correct schedule across non-trading days
- total_invested matches monthly amount × count
- total_units calculation matches hand example
- current_value matches final NAV × units
- XIRR is positive/negative according to outcome
- worst_drawdown matches known simple series
- stress-test method returns best and worst start windows
- life-happens scenario recomputes with skipped months or early stop
- empty or too-short history raises a controlled error

### Manual UX scenarios
- Default flow on mobile
- User picks minimum amount
- User picks maximum amount
- 1-year / 3-year / 5-year tenures
- Live API success and failure
- Fallback snapshot appears and is clearly labelled
- Start-date stress test with 3 comparison lines
- “Life happens” skip 1 month
- “Life happens” skip 3 months
- Stop early after 6 months
- Incorrect format in the source data fails loudly
- Screen 3 comprehension check catches misunderstanding

## Risks and mitigations
- API down or rate-limited:
  - fallback snapshot and visible error state
- Wrong numbers:
  - all formulas in one calc module with unit tests
- Confusing copy:
  - short plain-language lines and comprehension checks
- Overclaiming:
  - disclaimers and optional cut-first redemption line
- Mobile layout issues:
  - narrow center column, large controls, only one core action per screen

## Deployment steps (Streamlit Community Cloud)
1. Push public repo to GitHub
2. Add requirements.txt with exact package versions
3. Ensure app entry is app.py
4. Create a Streamlit Community Cloud app linked to the repo
5. Confirm app runs with fallback snapshot when data fetch fails
6. Verify all disclaimers remain visible on every screen
7. Test in a browser on mobile viewport
8. Record the chosen fund, source URL, and as-of date in README

## Final decision
Keep the flow narrow, transparent, and educational. The optional depth should stay clearly optional and cuttable. The prototype validates the confidence-first story without pretending to be a real financial product.

Summary under 300 words:

This revision keeps one user journey and max three screens while adding optional depth that is easy to cut: a stress-test comparison across best/worst start dates, a “life happens” skip/stop toggle, and an illustrative affordability band. The calculation spec now covers exact date parsing for YYYY-MM-DD, non-trading-day roll-back logic, unit accumulation, current value, XIRR, and a precise drawdown definition for portfolios with ongoing contributions. The stress test defines “best” and “worst” by final XIRR over the same tenure and explains the efficient windowed computation. The data layer explicitly rejects invalid date formats instead of auto-detecting them, and it uses st.cache_data plus a committed fallback snapshot to handle API failure cleanly. The build plan stays within roughly seven hours, with cut-first items if time is tight. The test plan includes unit tests for each new calculation and manual UX scenarios for the optional features. Out of scope remains fixed: no multi-fund flow, no AI, no gamification, no social features, and no real brokerage/KYC/payment flow.