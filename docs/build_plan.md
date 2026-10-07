## Plan summary

- Scope
  - In: first-job salaried beginner flow, single direct-growth Nifty 50 fund after browser verification of the exact mfapi.in scheme code, default ₹500 SIP, 1/3/5-year choices, and a 3-screen educational journey with visible source + disclaimer.
  - Out: real KYC, brokerage, payments, multiple funds, social features, live portfolio imports, support/withdrawal flows, and any recommendation language.

- Calculation spec
  - Use monthly SIP backtest against historical NAV dates; each instalment is assigned to the nearest valid NAV date on or before the contribution date, using the same monthly schedule for all users.
  - Accumulate units as amount ÷ NAV for each instalment, sum units, and value at “as of” date as total units × current NAV.
  - Compute XIRR using the cash-flow series: negative instalments for each contribution date and a final positive value at the as-of date.
  - Worst drawdown = largest peak-to-trough fall in portfolio value over the backtest window, expressed in rupees and percent; show plain-language copy like “your portfolio value fell by X% from its highest point before recovering.”

- Data layer
  - Fetch from mfapi.in search endpoint and exact fund scheme details, then confirm the scheme name/code in a browser before locking it.
  - Parse date strings as YYYY-MM-DD, normalize invalid or missing dates, and store a committed fallback snapshot in the repo.
  - Cache live fetches via st.cache_data, show a clear loading/error state, and if live data fails, show the fallback snapshot with visible last-success timestamp and source note.
  - Refresh snapshot by re-running the fetch, validating the result, and replacing the fallback file only after a clean parse.

- File structure
  - app.py: Streamlit shell and screens
  - calc.py: SIP backtest, XIRR, drawdown, helpers
  - data.py: mfapi fetch, parsing, fallback snapshot, error handling
  - data/nav_snapshot.json: committed fallback data
  - tests/: unit tests and manual eval script
  - requirements.txt
  - `README.md`

- Screen-by-screen spec
  - Screen 1: “Start small” — amount slider or number input, tenor chips (1/3/5 years), inline help copy, validation, and clear labels that this is a simulation.
  - Screen 2: “What would have happened” — backtest summary with invested value, current value, XIRR, worst dip, and a simple chart; keep wording plain-language and visible disclaimers on every screen.
  - Screen 3: “Check and start” — 2 short comprehension questions before simulated confirmation, then a confirmation state that says no real money moves and a short note that redemption timing is “typical and fund-specific, not a promise.” If the team is nervous about overclaiming, cut the redemption line entirely.

- Build sequence
  1. Data verification and contract lock — 30–45 min
  2. Calculation module with hand-checkable examples — 60–90 min
  3. Screen 1 + validation — 45–60 min
  4. Screen 2 backtest + chart — 60–90 min
  5. Screen 3 + comprehension checks + disclaimers — 30–45 min
  6. Fallback and error states + polish — 30–45 min
  7. Manual UX test + small adjustment pass — 30–45 min
  Total: about 4.5–5 hours

- Test plan
  - Unit tests: SIP schedule generation, non-trading-day rollover, unit accumulation, current value, XIRR, worst drawdown, empty data, tenure longer than history, zero/negative input protection.
  - Manual UX script: 8–10 scenarios covering default values, amount bounds, year choices, live-data failure, fallback snapshot, comprehension questions, longest-history edge case, and mobile layout review.

- Risks
  - API down or rate-limited — mitigation: fallback snapshot and visible error state
  - Sleeping Streamlit app or cold start — mitigation: keep app lightweight and source file small
  - Wrong numbers — mitigation: fixed, hand-verified calculation module + unit tests
  - Confusing copy — mitigation: plain-language labels and comprehension checks
  - Mobile layout feels crowded — mitigation: narrow center column, large touch controls, only 3 screens

- Deployment
  - Push to public GitHub repo
  - Create Streamlit Community Cloud app pointing to repo main branch
  - Add requirements.txt and all repo files
  - Set app entry to app.py
  - Confirm data fetch and fallback work in community environment
  - Keep disclaimers visible on every screen and document the selected fund and source in the README

## Checklist

- [ ] Final scope
- [ ] Calculation spec
- [ ] Data layer plan
- [ ] File structure
- [ ] Screen-by-screen spec
- [ ] Build sequence
- [ ] Test plan
- [ ] Risk plan
- [ ] Deployment steps