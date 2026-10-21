"""Guard: routes that must never come back.

Covers two retirements that are easy to undo by accident:

  /cron-twitter      - was a PUBLIC GET on the deployed site that posted the
                       day's picks to X via x_poster.post_daily_scan_to_twitter().
                       Any unauthenticated caller could trigger a post.
  /cron, /cron-      - looked like scans but never scanned. They only read
    cron-afternoon     ai_earnings_today.html and returned a freshness string.

Also asserts there is no X code surface left in the app.

Uses the Flask test client so it never touches the live site - a real GET
against a deployed posting route would attempt a real post.

Run:  python verify_routes.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# Resolve scanner_web.py relative to THIS SCRIPT, never to the current working
# directory. A stale copy of scanner_web.py lives in the CTO session workspace
# and still contains the old X route; importing by bare name picked that up and
# produced a pass/fail verdict about a file that is not the one being deployed.
sys.path.insert(0, HERE)
for _stale in list(sys.modules):
    if _stale == "scanner_web":
        del sys.modules[_stale]

from scanner_web import app

SCANNER_WEB = os.path.join(HERE, "scanner_web.py")

client = app.test_client()

# Routes that must 404. The reason is documented above.
FORBIDDEN_ROUTES = {
    "/cron-twitter": "public route that posted to X",
    "/cron": "dead route that never scanned",
    "/cron-afternoon": "dead route that never scanned",
}

# Routes that MUST keep working.
REQUIRED_ROUTES = {
    "/cron-price-alerts": "intentionally left in place, disabled and harmless",
}

# X surface that must not appear in the source.
FORBIDDEN_TOKENS = (
    "x_poster",
    "post_daily_scan_to_twitter",
    "api.twitter",
    "X_API_KEY",
    "tweepy",
)

failed = False

print("=== retired routes must be absent from the route map ===")
url_map = {r.rule for r in app.url_map.iter_rules()}
for path, why in FORBIDDEN_ROUTES.items():
    in_map = path in url_map
    resp = client.get(path)
    ok = (not in_map) and resp.status_code == 404
    print(f"  {'PASS' if ok else 'FAIL'}  {path:<18} in_map={in_map!s:<5} "
          f"GET={resp.status_code} (expect 404) - {why}")
    if not ok:
        failed = True

print("\n=== routes that must still exist ===")
for path, why in REQUIRED_ROUTES.items():
    ok = path in url_map
    print(f"  {'PASS' if ok else 'FAIL'}  {path:<18} in_map={ok} - {why}")
    if not ok:
        failed = True

print("\n=== no X code surface in scanner_web.py ===")
with open(SCANNER_WEB, encoding="utf-8") as fh:
    lines = fh.read().splitlines()

for token in FORBIDDEN_TOKENS:
    hits = [
        (i + 1, ln.strip())
        for i, ln in enumerate(lines)
        if token in ln and not ln.lstrip().startswith("#")
    ]
    print(f"  {'PASS' if not hits else 'FAIL'}  {token}: "
          f"{len(hits)} non-comment reference(s)")
    for lineno, text in hits:
        print(f"          line {lineno}: {text[:90]}")
    if hits:
        failed = True

print("\n=== result ===")
if failed:
    print("FAILED - a retired route or X code path is reachable again")
    sys.exit(1)
print("PASSED - retired routes gone, no X posting path")