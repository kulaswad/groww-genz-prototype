# Groww for Gen Z — case-study thinking plan

## Problem framing

The problem is not that Gen Z needs a separate investing app. It is that a first-time investor has little room for error: uncertain cash flow, low confidence, and limited investing context make an unclear or high-stakes moment feel like a reason not to start. Groww's beginner-friendly surface is a useful starting point, but a smooth first buy alone may not earn lasting trust. The product opportunity is to make a small first step understandable and reversible-looking without misrepresenting real investment risk. Treat the reported withdrawal, support, performance, and reporting complaints as hypotheses, not representative Gen Z evidence: the sources are anecdotal, age is unknown, and traders may be over-represented.

**Opinion:** Prioritize confidence and clarity at the first recurring-investment decision, not a Gen-Z visual reskin or social/trading features. A five-hour prototype cannot prove trust or retention, but it can test whether plain-language context helps a novice make an informed simulated choice.

## Target sub-segments

| Segment | Income pattern and mindset | Start barrier | What may make them stay |
|---|---|---|---|
| Student / pocket-money investor | Small, irregular allowance or stipend; wants to learn without risking meaningful money | No surplus, assumes investing requires a large minimum, fears loss | Tiny, optional practice steps and visible learning progress |
| First-job salaried investor | Predictable monthly salary, but competing expenses; wants to build independence | Jargon, uncertainty about how much is safe, decision paralysis | Simple recurring setup, transparent status, confidence that money and outcomes are trackable |
| Gig / part-time earner | Variable weekly/monthly cash flow; values flexibility | Fixed SIP dates/amounts feel brittle; worries about needing cash suddenly | Flexible contributions, clear pause/withdrawal terms, reliable support |

These are behavior-based hypotheses, not mutually exclusive demographic categories.

## Pain-point hypotheses (confidence is about current evidence)

| Hypothesis | Confidence | Cheap validation with 3–5 people |
|---|---|---|
| Unclear risk and fear of losing money prevent a first investment | Medium | Ask what they think could happen to ₹500 over a year; probe what wording changes their confidence |
| Jargon and too many choices create decision paralysis | Medium | Observe a participant explain a fund card in their own words |
| Uncertainty about the minimum / whether a small amount is worthwhile blocks starting | Low | Ask them to choose an amount and narrate their hesitation |
| Irregular income makes a fixed monthly commitment feel unsafe | Medium | Compare student, salaried, and gig participants; ask how they handle a low-cash month |
| Trust is lost when withdrawal timing, support, or transaction status is opaque | Low | Ask for a recent money-app trust incident and what status/support information they expected |
| Social-media FOMO nudges novices toward unsuitable or rushed choices | Low | Ask where their last investment idea came from and what they checked before acting |
| No simple habit/feedback loop causes drop-off after initial curiosity | Low | Ask what existing monthly money habit they sustain and why |
| Users outgrow beginner guidance and want consolidated, credible performance reporting | Low | Ask how they currently track investments and which number (returns, XIRR, holdings) they trust |

Do not treat three to five conversations as prevalence research. Use them to find confusing language, disconfirm assumptions, and choose an evaluation task.

## Assumptions

**Safe:** The prototype is educational/simulated; no KYC, brokerage, payment, or real order execution; users can leave without investing; market history is not a forecast; data source and as-of time are visible; simulated account values are clearly distinguished from real market data.

**Risky:** A first-job salaried novice is the best primary segment; understanding a small recurring investment is more valuable than solving a trust/support failure; real historical fund data makes the decision more credible rather than more intimidating; a fixed monthly contribution is suitable enough for a prototype; public API availability and terms permit the demo's use; one selected fund/index is an acceptable teaching proxy.

## Scope candidates for a five-hour build

**In scope:** One mobile-friendly Streamlit flow for a first-job novice; three screens maximum (choose a small monthly amount and horizon → inspect one real fund's historical NAV and plain-language risk context → confirm a simulated SIP and see a simulated summary); one real mutual-fund NAV series; a clear timestamp/source and an in-repo fallback snapshot; explicit no-advice/no-real-money labels; basic validation for amount/horizon; one concise comprehension check.

**Out of scope:** Real account/KYC/orders/payments (unsafe and infeasible); withdrawal execution/support workflows (important trust problem but cannot be credibly simulated in this time); multiple asset classes/fund discovery (dilutes the test); social feed, gamification, AI recommendations, advanced analytics (not needed to validate the core journey); account aggregation and live portfolio imports (no backend); live intraday/index feeds unless NAV integration proves unusable.

## Three product bets

1. **First Investment, Without Guesswork (recommended):** Convert a small monthly amount into an understandable, simulated first SIP decision, with real NAV history, plain-language context, and transparent simulation boundaries. Target: first-job salaried novice. Risk: historical data and education may not address the deeper trust failure or translate to real behavior. Buildable in Streamlit in the available time.
2. **Flexible-by-Default Investing:** Let variable earners explore a contribution they can pause or vary, with explicit liquidity trade-offs. Target: gig/part-time earners. Risk: a convincing flexible-SIP policy and withdrawal model require product/legal accuracy the prototype cannot establish.
3. **Trust Ledger:** Make investment, withdrawal, and support states/timelines unusually transparent. Target: anyone anxious about money movement. Risk: the strongest anecdotal pain point needs operational integrations and reliable service promises, neither of which a static demo can substantiate.

Choose bet 1 because it tests the most buildable, observable first-time-investor decision without pretending to fix brokerage operations. Treat it as a learning prototype, not a claim that trust concerns are solved.

## Success and evaluation

**Primary metric:** Share of first-time users who complete the simulated plan *and* correctly answer a short check that historical returns are not guaranteed and the prototype did not invest real money.

**Supporting metrics:** (1) Task completion without facilitator rescue; (2) time and number of misunderstood terms / backtracks; (3) stated confidence before vs. after, interpreted qualitatively rather than as proof of retention. A later live product would also measure eligible-user activation and 30-day recurring-plan retention, plus support/withdrawal complaint rates; the prototype cannot measure these reliably.

**Cheap evals:** 3–5 moderated task-based sessions across the segments; a scripted comprehension check; verify calculations against hand-worked NAV examples; test live API success, timeout/error, and fallback paths; check that source/as-of and simulated-vs-real labels remain visible. Capture the actual Copilot prompts used during implementation as a separate artifact; do not invent a prompt history.

## Data fit

Use mfapi.in / AMFI-derived public NAV history for one clearly named, plausible mutual-fund scheme to ground the chart and the simulated historical calculation. Keep source URL, retrieval/as-of date, and a small cached fallback snapshot in the repository. Show only historical observations and a transparent hypothetical calculation; label it non-predictive. If that integration fails, use a narrowly scoped Nifty index history only if the data source and instrument representation remain clear.

Real data adds little to onboarding language, goal/amount inputs, comprehension checks, or simulated account identity/balance/transactions. Do not add live quotes, multiple fund catalogs, holdings aggregation, or elaborate return metrics to make the demo seem more real.

## Decisions confirmed

1. **Answered:** You can access a mix of students, first-job salaried people, and gig/part-time earners.
2. **Answered:** Center the prototype on a simulated SIP in one named mutual fund; no investment recommendation or real order.
3. **Answered:** Prioritize first-investment confidence; it is more feasible to test honestly in a prototype.
4. **Answered:** Select one suitable mutual-fund scheme from mfapi.in / AMFI-derived NAV data.
5. **Answered:** A public, no-login Streamlit app is acceptable with a visible simulation disclaimer.

The working direction is therefore a confidence-first, simulated first-SIP journey for a mixed interview sample, grounded in one suitable mfapi.in / AMFI-derived NAV history and clearly labeled as educational—not advice or a real order.

## Execution order after answers

1. Resolve segment, core bet, and data choice from the answers.
2. Lock one core journey and the three-screen boundary; write the 300–700 word note and evaluation criteria.
3. Implement and host the Streamlit prototype with live data plus a repository fallback; preserve a record of actual Copilot prompts.
4. Run the stated evals, fix critical confusion/data failures, and deliver the app link with the case-study artifacts.
