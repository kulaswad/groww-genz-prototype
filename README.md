# First Step

First Step is a case-study prototype for first-job salaried people aged 22-26. It walks through one hypothetical monthly SIP in the Motilal Oswal Nifty 50 Index Fund - Direct Plan - Growth. Fund NAV history is real; payments, units, portfolio values, and the plan are simulated. The prototype does not recommend an investment or move money.

## Run locally

```powershell
py -m pip install -r requirements.txt
streamlit run app.py
```

The app tries the live mfapi.in endpoint first and falls back to `data/nav_snapshot.json` if the fetch fails. Dates from mfapi.in are parsed strictly as `DD-MM-YYYY`. The snapshot records the scheme, retrieval time, and source URL.

## Assumptions

- Default contribution: Rs 500 per month; selectable range: Rs 100-Rs 5,000.
- Contributions are scheduled for the 5th of each month, or the next available NAV date.
- Available horizons are 1, 3, and 5 years; 3 years is the default.
- The simulation ends on the latest NAV date in the loaded data, never today's date.
- One fund and one historical path are shown; all contributions and account values are hypothetical.

## Limitations

This fund's available history begins in December 2019, about 6.8 years before the current snapshot. Historical outcomes are not forecasts, and this single-fund simulation cannot represent every real investor experience. NAV history depends on mfapi.in availability; a saved snapshot may be older than live data.

Illustration only. Past performance is not a guarantee. This is not investment advice. Independent case-study prototype, not affiliated with Groww.