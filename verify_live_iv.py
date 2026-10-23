"""Wait for Railway to actually serve the IV fix, then prove it.

A 200 proves the service is up. It does not prove the new commit deployed,
and Railway has paused builds before - which cost Tyler an hour of being
told "fixed" while the running site was still the old build. So this polls
for a marker that only exists in the new artifact and reports what it finds.
"""
import io
import json
import sys
import time
import urllib.request

URL = 'https://aismarketcap.com/'
MARK = '<script>var rowsData='


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
        rows = parse(html)
        if rows:
            both = [r for r in rows if r.get('iv') and r.get('pe_upside')]
            same = [r for r in both if r.get('iv') == r.get('pe_upside')]
            if not same:
                print('new build live on attempt %d' % attempt)
                break
            print('  attempt %d: old build still live (iv==upside %d/%d)'
                  % (attempt, len(same), len(both)))
        else:
            print('  attempt %d: rowsData not found yet' % attempt)
    except Exception as e:
        print('  attempt %d: %s' % (attempt, e))
    time.sleep(25)

if not html:
    print('FAIL could not fetch')
    sys.exit(1)

rows = parse(html)
if not rows:
    print('FAIL rowsData never appeared')
    sys.exit(1)

both = [r for r in rows if r.get('iv') and r.get('pe_upside')]
same = [r for r in both if r.get('iv') == r.get('pe_upside')]
have = [r['iv'] for r in rows if r.get('iv')]
bad = [v for v in have if not 10 <= v <= 250]

print('')
print('LIVE rows                    : %d' % len(rows))
print('LIVE iv == pe_upside         : %d/%d   (was 100/100)' % (len(same), len(both)))
print('LIVE iv populated            : %d/%d' % (len(have), len(rows)))
print('LIVE iv outside 10-250%%      : %d' % len(bad))
print('LIVE n/a rendered for gaps   : %s' % ('>n/a<' in html))
print('LIVE samples                 : %s'
      % [(r['ticker'], r.get('iv'), r.get('pe_upside')) for r in rows[:6]])

ok = (not same) and len(have) >= len(rows) * 0.5 and not bad
print('')
print('RESULT: %s' % ('LIVE IS SERVING REAL IMPLIED VOLATILITY' if ok
                      else 'LIVE STILL HAS THE OLD BUILD'))
sys.exit(0 if ok else 1)