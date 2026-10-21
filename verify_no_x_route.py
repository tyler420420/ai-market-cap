"""Verify /cron-twitter is actually gone from the Flask app.

Uses the Flask test client so nothing touches the live site - a real GET
against the deployed route would attempt a real post.

Run:  python verify_no_x_route.py
"""
import sys

from scanner_web import app

client = app.test_client()

checks = [
    ("/cron-twitter", "the route that posted to X"),
]

print("=== route removal ===")
url_map = {r.rule for r in app.url_map.iter_rules()}
print(f"  /cron-twitter present in url_map: {'/cron-twitter' in url_map}")

failed = False
for path, why in checks:
    resp = client.get(path)
    ok = resp.status_code == 404
    print(f"  {'PASS' if ok else 'FAIL'}  GET {path} -> {resp.status_code}  (expect 404) - {why}")
    if not ok:
        failed = True

print("\n=== X code surface in the app object ===")
src = open("scanner_web.py", encoding="utf-8").read()
for needle in ("x_poster", "post_daily_scan_to_twitter", "api.twitter", "X_API_KEY", "tweepy"):
    code_hits = [
        ln for ln in src.splitlines()
        if needle in ln and not ln.lstrip().startswith("#")
    ]
    status = "PASS" if not code_hits else "FAIL"
    print(f"  {status}  {needle}: {len(code_hits)} non-comment references")
    if code_hits:
        failed = True

print("\n=== result ===")
if failed:
    print("FAILED - X surface still reachable")
    sys.exit(1)
print("PASSED - no X posting path in the app")