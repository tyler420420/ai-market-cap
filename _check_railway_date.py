import datetime, urllib.request

# Check what Railway's cron sees vs what it should be
# Railway container: what date does it use?
# If container clock is UTC, 6:30 AM PT = 1:30 PM UTC
# Cron fires at: depends on Railway's configured timezone

# Today is June 18 PT
today_pt = datetime.date(2026, 6, 18)
mu_earnings = datetime.date(2026, 6, 24)

# If cron ran at 6:30 AM PT on June 18:
# UTC time would be 1:30 PM UTC on June 18
# datetime.now().date() on Railway would be June 18 UTC
# days_to_earnings = June 24 - June 18 = 6

# If Railway fires at 6:30 AM UTC (misconfigured = NOT PT):
# UTC time June 18 6:30 AM = June 17 11:30 PM PT (previous day!)
# datetime.now().date() on Railway = June 18
# days = 6

# If Railway fires at 6:30 AM PT but server clock is WRONG by 1 day:
# datetime.now().date() = June 17
# days = June 24 - June 17 = 7

print("June 24 - June 17 = 7 (if Railway date is June 17)")
print("June 24 - June 18 = 6 (if Railway date is June 18)")

# Check: what does Railway actually see right now?
import urllib.request
req = urllib.request.Request('https://aismarketcap.com', headers={'User-Agent': 'Mozilla/5.0'})
r = urllib.request.urlopen(req)
html = r.read().decode('utf-8')

import re
# Get full table rows to find MU price
m = re.search(r'MU.*?current.*?\$([0-9,]+)', html, re.DOTALL)
if m:
    print("MU price pattern:", m.group()[:100])

# Let's get raw MU price from the table
tds = re.findall(r'<td[^>]*>(.*?)</td>', html)
# MU is the second stock (index 20-39)
for i, td in enumerate(tds):
    if 'MU' in td and 'Micron' not in td:
        print(f"MU ticker cell {i}: {td[:50]}")
        if i+5 < len(tds):
            print(f"  Days left: {tds[i+4][:50]}")
            print(f"  Current price: {tds[i+5][:50]}")
