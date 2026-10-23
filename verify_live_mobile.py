"""Prove the LIVE site is serving the new build.

A 200 from /api/visitors proves the service is up. It does not prove the
new commit deployed. These markers only exist in the redesign, so their
absence means Railway is still serving the old artifact.

Also re-checks the two data facts, on the live page, so the report is about
what customers actually get.
"""
import io
import json
import re
import sys
import time
import urllib.request

URL = 'https://aismarketcap.com/'
MARKERS = [
    ('grid card layout', '#stockTable tbody tr{display:grid'),
    ('six-column track', 'grid-template-columns:repeat(6,1fr'),
    ('label stack disabled', '#stockTable td::before{content:none!important}'),
    ('target line break kept', 'td:nth-child(9)>br'),
    ('price divider suppressed on mobile', 'border-right:0!important'),
    ('More toggle present', 'function addMobileMore(){'),
    ('old flex stack is GONE', None),   # inverted check
]


def fetch():
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
    # decode() explicitly: io.open() cannot take a bytes object, and letting
    # it fail here looks like the site being down rather than a bad call.
    return urllib.request.urlopen(req, timeout=40).read().decode(
        'utf-8', 'replace')


html = None
for attempt in range(1, 13):
    try:
        html = fetch()
    except Exception as e:
        print('  attempt %d: fetch failed (%s)' % (attempt, e))
        html = None
    if html and '#stockTable tbody tr{display:grid' in html:
        print('new build detected on attempt %d' % attempt)
        break
    print('  attempt %d: new build not live yet' % attempt)
    time.sleep(20)

if html is None:
    print('FAIL could not fetch the live page')
    sys.exit(1)

fails = 0
for name, marker in MARKERS:
    if marker is None:
        ok = 'td{display:flex;justify-content:space-between' not in html
    else:
        ok = marker in html
    if not ok:
        fails += 1
    print('%-4s %s' % ('PASS' if ok else 'FAIL', name))

# the old mobile stack must really be gone
print('%-4s old mobile stack removed'
      % ('PASS' if 'td{display:flex;justify-content:space-between' not in html
         else 'FAIL'))

# company names must no longer be cut at 12 chars
m = re.search(r'var rowsData=(\{.*?\});', html, re.S)
if m:
    rows = json.loads(m.group(1))
    cut = [r['company_name'] for r in rows
           if len(r['company_name']) == 12 and ' ' in r['company_name'][-2:]]
    print('%-4s company names no longer 12-char cut (bad=%d)'
          % ('PASS' if not cut else 'FAIL', len(cut)))
    print('     samples: %s' % [r['company_name'] for r in rows[:4]])
else:
    fails += 1
    print('FAIL could not locate rowsData on the live page')

print('')
print('%d marker(s) failing' % fails)
sys.exit(1 if fails else 0)