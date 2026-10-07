import requests, datetime as D
from datetime import date

d = requests.get('https://api.mfapi.in/mf/147794', timeout=30).json()['data']
nav = sorted((D.datetime.strptime(x['date'], '%d-%m-%Y').date(), float(x['nav'])) for x in d)

def nav_on_or_after(t):
    return next((dt, v) for dt, v in nav if dt >= t)

# --- fill these from the app screen you are checking ---
AMOUNT, FIRST, MONTHS = 500, date(2023, 11, 5), 36

units = 0
for i in range(MONTHS):
    m = FIRST.month - 1 + i
    y, mo = FIRST.year + m // 12, m % 12 + 1
    units += AMOUNT / nav_on_or_after(date(y, mo, 5))[1]
last_date, last_nav = nav[-1]
print('Put in:', AMOUNT * MONTHS, '| Value:', round(units * last_nav, 2), '| as of', last_date)

# Panic-test check: biggest fall from a peak (lump sum)
peak = (nav[0][0], nav[0][1]); worst = (0, None, None)
for dt, v in nav:
    if v > peak[1]: peak = (dt, v)
    fall = (peak[1] - v) / peak[1]
    if fall > worst[0]: worst = (fall, peak[0], dt)
print('Biggest fall: %.2f%% from %s to %s' % (worst[0] * 100, worst[1], worst[2]))