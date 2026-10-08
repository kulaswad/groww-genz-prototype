import argparse
import requests
from datetime import date, datetime

p = argparse.ArgumentParser()
p.add_argument('--amount', type=float, default=500)
p.add_argument('--first', required=True, help='first scheduled date, YYYY-MM-DD')
p.add_argument('--months', type=int, required=True)
a = p.parse_args()

first = datetime.strptime(a.first, '%Y-%m-%d').date()
rows = requests.get('https://api.mfapi.in/mf/147794', timeout=30).json()['data']
nav = sorted((datetime.strptime(r['date'], '%d-%m-%Y').date(), float(r['nav'])) for r in rows)

def on_or_after(t):
    # next NAV date on or after the scheduled date
    return next((d, v) for d, v in nav if d >= t)

units = 0.0
for i in range(a.months):
    m = first.month - 1 + i
    y, mo = first.year + m // 12, m % 12 + 1
    d, v = on_or_after(date(y, mo, first.day))
    if i == 0:
        print('First scheduled:', first, '| first NAV date:', d, '| NAV:', v)
    units += a.amount / v

last_date, last_nav = nav[-1]
print('Months:', a.months, '| Put in:', round(a.amount * a.months),
      '| Value:', round(units * last_nav, 2), '| as of', last_date)