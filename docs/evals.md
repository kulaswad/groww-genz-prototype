EVAL LOG

Test 1: Automated checks
Do: run pytest -v
Expected: all tests pass
Result:
Notes:

Test 2: Panic test figures
Do: compare app with scripts/eval_check.py
Expected: 37.28% fall, 14 Jan to 23 Mar 2020
Result: Pass
Notes: app and script agree

Test 3: SIP value, 1 / 3 / 5 years
Do: Rs 500 per month in the app, then run the script with the same first date
Expected: value within Rs 1-2 of the script
Result:
Notes:

Test 4: Small change, Rs 50 per day, 1 year
Do: check the screen and compare with the script
Expected: Rs 1,500 per month, Rs 18,000 put in
Result:
Notes:

Test 5: Amount limits
Do: enter Rs 99 and Rs 5,001 on Start small
Expected: blocked or clamped, with a clear message
Result:
Notes:

Test 6: Small change cap
Do: enter a custom Rs 10,000 per month
Expected: clamped to Rs 5,000, with a message
Result:
Notes:

Test 7: Bad timing, 5 years
Do: choose a 5-year tenure
Expected: friendly message if there are few windows
Result:
Notes:

Test 8: Offline
Do: turn Wi-Fi off, reload
Expected: snapshot banner, no crash
Result:
Notes:

Test 9: Back button and refresh
Do: press back and refresh mid-flow
Expected: no broken state
Result:
Notes:

Test 10: Trust and compliance
Do: open every screen
Expected: disclaimer, "not affiliated with Groww", as-of date
Result:
Notes:

Test 11: Tone
Do: read all copy
Expected: no "you should invest", no shaming for choosing Sell
Result:
Notes:

Test 12: Mobile
Do: 390px window, then your real phone
Expected: no sideways scroll, readable dark theme
Result:
Notes:

Test 13: Hosted app
Do: incognito window, all three modules on the live URL
Expected: all modules work
Result:
Notes: Module C failed at first on the hosted app; fixed by (write what you did)

Test 14: Comprehension (3 people aged 20-26)
Do: they try the panic test and Start small
Expected: they understand, nobody thinks real money moved
Result:
Notes: (their words)

Test 15: First impression (2 people)
Do: show the home screen for 10 seconds
Expected: they can say what the app does
Result:
Notes: (their words)

KNOWN ISSUES, NOT FIXED
-