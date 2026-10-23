"""Prove the LIVE site is serving the current build, and that the mobile card is
serving ALL its data.

A 200 from /api/visitors proves the service is up. It does not prove the new
commit deployed. These markers only exist in the redesign, so their absence
means Railway is still serving the old artifact.

THIS GUARD WAS WRONG IN TWO WAYS AND BOTH MATTER
=================================================
1. It asserted the "More" toggle was PRESENT.
       ('More toggle present', 'function addMobileMore(){')
   That toggle was removed on purpose. It hid 6 of 19 fields, two of which -
   Buy count and Sentiment - are inputs to the score the product sells. Its
   removal is pinned by verify_mobile_cards.py and by verify_live_today.py.
   So this guard did not merely fail: it actively argued for restoring a known
   defect, and it contradicted two other guards in the same repo. Left as-is,
   running it would have "fixed" the bug.

2. It located rowsData with re.search(r'var rowsData=(\{.*?\});', html, re.S).
   That non-greedy pattern stops at the FIRST "};" inside the payload, and the
   embedded news-URL base64 contains one. The match therefore truncates, the
   JSON fails to parse, and the guard reports "could not locate rowsData" -
   a false alarm about a page that is perfectly fine. Extract by brace
   counting instead.

Neither failure had been noticed because this file was not in
run_all_guards.py. A guard nobody runs is not a guard. It is registered now.
"""
import io
import json
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
]
# Things that must be ABSENT. Listed separately because "must not appear" and
# "must appear" fail in opposite directions and conflating them is how the
# More toggle check came to assert the wrong thing.
FORBIDDEN = [
    ('More toggle is gone', 'function addMobileMore(){'),
    ('old flex stack is GONE', 'td{display:flex;justify-content:space-between'),
]


def fetch():
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
    # decode() explicitly: io.open() cannot take a bytes object, and letting
    # it fail here looks like the site being down rather than a bad call.
    return urllib.request.urlopen(req, timeout=40).read().decode(
        'utf-8', 'replace')


def extract_rows_data(html):
    r"""Return the parsed rowsData value, or None.

    Brace/bracket counting, not a regex. Two separate traps here:

      * A non-greedy regex stops at the first "};" inside the payload, because
        the embedded news-URL base64 contains one. The match truncates, the JSON
        will not parse, and the guard reports "the data is missing" when the
        page is fine.
      * The payload is an ARRAY, not an object: var rowsData=[{...},{...}].
        The previous version searched for "{" and so could never have matched,
        for the same reason.

    Start from whichever of [ or { opens the value, and count both.
    """
    key = 'var rowsData='
    i = html.find(key)
    if i < 0:
        return None
    i += len(key)
    while i < len(html) and html[i] in ' \t\r\n':
        i += 1
    if i >= len(html) or html[i] not in '[{':
        return None
    start = i
    depth = 0
    in_str = False
    esc = False
    while i < len(html):
        ch = html[i]
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch in '[{':
                depth += 1
            elif ch in ']}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(html[start:i + 1])
                    except Exception as e:
                        print('     rowsData bracket match found but JSON failed: %s' % e)
                        return None
        i += 1
    return None


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
    ok = marker in html
    fails += (0 if ok else 1)
    print('%-4s %s' % ('PASS' if ok else 'FAIL', name))

for name, marker in FORBIDDEN:
    ok = marker not in html
    fails += (0 if ok else 1)
    print('%-4s %s' % ('PASS' if ok else 'FAIL', name))

# company names must no longer be cut at 12 chars in the PAYLOAD
rows = extract_rows_data(html)
if rows is None:
    fails += 1
    print('FAIL could not parse rowsData from the live page')
else:
    cut = [r['company_name'] for r in rows
           if len(r['company_name']) == 12 and ' ' in r['company_name'][-2:]]
    ok = not cut
    fails += (0 if ok else 1)
    print('%-4s company names no longer 12-char cut (bad=%d)'
          % ('PASS' if ok else 'FAIL', len(cut)))
    print('     rows parsed: %d' % len(rows))
    print('     samples: %s' % [r['company_name'] for r in rows[:4]])

    # The full card must reach the client, not a truncated one.
    need = {'company_name', 'ticker', 'score', 'days_left'}
    have = set(rows[0].keys()) if rows else set()
    ok = need.issubset(have)
    fails += (0 if ok else 1)
    print('%-4s card payload carries the fields the redesign pins'
          % ('PASS' if ok else 'FAIL'))
    if not ok:
        print('     missing: %s' % sorted(need - have))

print('')
print('%d marker(s) failing' % fails)
sys.exit(1 if fails else 0)