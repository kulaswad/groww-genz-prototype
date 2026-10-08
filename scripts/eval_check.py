import argparse
import datetime as D
from datetime import date

import requests


parser = argparse.ArgumentParser(description="Independently check SIP value against mfapi NAVs.")
parser.add_argument("--amount", type=float, default=500.0)
parser.add_argument("--first", type=date.fromisoformat, required=True, help="First scheduled instalment date (YYYY-MM-DD)")
parser.add_argument("--months", type=int, required=True, help="Number of monthly instalments")
args = parser.parse_args()

d = requests.get('https://api.mfapi.in/mf/147794', timeout=30).json()['data']
nav = sorted((D.datetime.strptime(x['date'], '%d-%m-%Y').date(), float(x['nav'])) for x in d)

def nav_on_or_after(t):
    return next((dt, v) for dt, v in nav if dt >= t)

AMOUNT, FIRST, MONTHS = 500, date(2025, 10, 5), 12

units = 0
first_nav_date, first_nav = None, None
for i in range(MONTHS):
    m = FIRST.month - 1 + i
    y, mo = FIRST.year + m // 12, m % 12 + 1
    scheduled_date = date(y, mo, FIRST.day)
    matched_date, matched_nav = nav_on_or_after(scheduled_date)
    if i == 0:
        first_nav_date, first_nav = matched_date, matched_nav
    units += AMOUNT / matched_nav
last_date, last_nav = nav[-1]
print(
    'Amount:', AMOUNT,
    '| Months:', MONTHS,
    '| First scheduled:', FIRST,
    '| First NAV date:', first_nav_date,
    '| First NAV:', first_nav,
    '| Put in:', AMOUNT * MONTHS,
    '| Value:', round(units * last_nav, 2),
    '| as of', last_date,
)

# Panic-test check: biggest fall from a peak (lump sum)
peak = (nav[0][0], nav[0][1]); worst = (0, None, None)
for dt, v in nav:
    if v > peak[1]: peak = (dt, v)
    fall = (peak[1] - v) / peak[1]
    if fall > worst[0]: worst = (fall, peak[0], dt)
print('Biggest fall: %.2f%% from %s to %s' % (worst[0] * 100, worst[1], worst[2]))