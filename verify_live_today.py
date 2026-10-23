"""Prove the live site serves every change from today's round.

A 200 proves the service is up. Each marker below exists ONLY in the new
artifact, so its absence means Railway is still serving the old build -
which has happened before, and looks identical to "working fine".

Also re-asserts the real implied volatility on the live page, because the
mobile redesign and the IV fix were separate commits and either could be the
one still pending.
"""
import io
import json
import sys
import time
import urllib.request

URL = 'https://aismarketcap.com/'
MARK = '<script>var rowsData='

# (label, marker that exists only in the new artifact)
MARKERS = [
    ('mobile card is a grid', '#stockTable tbody tr{display:grid', True),
    ('no More toggle', 'mob-more', False),
    ('footer says analysts', "content:' analysts'", True),
    ('footer says IV', "content:' IV'", True),
    ('non-subscriber gate class', 'classList.add("nonsub")', True),
    ("Today's Pick hidden for non-subs", 'body.nonsub #pro-targets{display:none!important}', True),
    ('subscriber sees Refresh', 'sb.textContent="Refresh"', True),
    ('popup no longer sells Top 5', 'Top 5 ranked plays', False),
    ('popup sells the daily email', 'One email every morning before the open', True),
    ('IV n/a fallback shipped', "r.iv?r.iv", True),
]

INVERTED = []


def fetch():
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
    return urllib.request.urlopen(req, timeout=45).read().decode('utf-8', 'replace')


def parse(page):
    i = page.find(MARK)
    if i < 0:
        return None
    ds = page[i + len(MARK):page.find('</script>', i)]
    depth, in_str, esc, end = 0, False, False, 0
    for j, ch in enumerate(ds):
        if esc:
            esc = False
            continue
        if ch == '\\':
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch in '{[':
            depth += 1
        elif ch in '}]':
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    return json.loads(ds[:end]) if end else None


html = None
for attempt in range(1, 16):
    try:
        html = fetch()
        if html and "content:' analysts'" in html and 'Top 5 ranked plays' not in html:
            print('new build live on attempt %d' % attempt)
            break
        print('  attempt %d: new build not live yet' % attempt)
    except Exception as e:
        print('  attempt %d: %s' % (attempt, e))
    time.sleep(25)

if not html:
    print('FAIL could not fetch')
    sys.exit(1)

fails = 0
for name, marker, present in MARKERS + INVERTED:
    ok = (marker in html) if present else (marker not in html)
    if not ok:
        fails += 1
    print('%-4s %s' % ('PASS' if ok else 'FAIL', name))

rows = parse(html)
if not rows:
    print('FAIL rowsData not parseable')
    sys.exit(1)
both = [r for r in rows if r.get('iv') and r.get('pe_upside')]
same = [r for r in both if r.get('iv') == r.get('pe_upside')]
have = [r['iv'] for r in rows if r.get('iv')]
iv_ok = not same and len(have) >= len(rows) * 0.5
if not iv_ok:
    fails += 1
print('%-4s live IV is real (iv==upside %d/%d, populated %d/%d)'
      % ('PASS' if iv_ok else 'FAIL', len(same), len(both), len(have), len(rows)))
print('     samples %s'
      % [(r['ticker'], r.get('iv'), r.get('pe_upside')) for r in rows[:4]])

print('')
print('RESULT: %s' % ('LIVE SERVES TODAY\'S WORK' if not fails
                      else '%d MARKER(S) NOT LIVE' % fails))
sys.exit(1 if fails else 0)