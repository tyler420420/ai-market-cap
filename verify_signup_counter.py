#!/usr/bin/env python3
"""The free-signup counter must be DEPLOY-DURABLE and PII-FREE.

WHY THIS EXISTS
---------------
Free signups were captured onto Railway's container disk and destroyed on
every redeploy. The only way to count them was the export route, which needs
a token that was never set, so the funnel's `users` link read UNKNOWN - and
UNKNOWN is indistinguishable from "nobody is signing up", which is how a dead
funnel link hides for months.

The fix is an aggregate counter: ONE integer, committed, shipped with the
code, seeding the container's counter at boot so a redeploy cannot reset it.

WHAT IS ASSERTED
1. signup_baseline.json exists, is TRACKED in git, and holds an integer.
2. The container-side file is NOT tracked - it is ephemeral by design.
3. Neither file holds PII: no addresses, and no hashes of addresses (a
   salted SHA-256 of an email is still brute-forceable, so it stays out).
4. scanner_web.py seeds the container counter from the committed total, and
   increments it only for a NEW address.
5. measure_funnel.py reads the durable aggregate, NOT the ephemeral export.
6. sync_signup_counter.py is monotonic - it can only move the number UP.
"""
import io
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE

fails = []
passes = []


def check(name, ok, detail=""):
    (passes if ok else fails).append(name)
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name,
                           ("   -- " + detail) if (detail and not ok) else ""))


def tracked(rel):
    p = subprocess.run(["git", "-C", str(REPO), "ls-files", "--error-unmatch", rel],
                       capture_output=True, text=True)
    return p.returncode == 0


def ignored(rel):
    p = subprocess.run(["git", "-C", str(REPO), "check-ignore", "-q", rel])
    return p.returncode == 0


print("=== 1. the committed baseline ===")
BASE = HERE / "signup_baseline.json"
check("signup_baseline.json exists", BASE.exists())
base = {}
if BASE.exists():
    try:
        base = json.loads(BASE.read_text(encoding="utf-8"))
    except Exception as e:
        check("signup_baseline.json is valid JSON", False, str(e))
if base:
    check("signup_baseline.json is valid JSON", True)
    check("it holds an integer total", isinstance(base.get("total"), int),
          "total=%r" % (base.get("total"),))
    check("it is TRACKED in git (survives redeploy)", tracked("signup_baseline.json"))
    check("it says what it is in the note", "aggregate" in (base.get("note") or "").lower())

print("\n=== 2. no PII, in either file ===")
for path in (BASE, HERE / "signup_counts.json"):
    if not path.exists():
        continue
    raw = path.read_text(encoding="utf-8", errors="replace")
    check("%s holds no email address" % path.name, "@" not in raw,
          "found an '@' in a file that must carry no addresses")
    # A 32+ hex run is a hash of something. A salted SHA-256 of an email is
    # still brute-forceable, so it counts as PII and must not be committed.
    hexes = [h for h in re.findall(r"[0-9a-fA-F]{32,}", raw) if not re.fullmatch(r"[0-9a-fA-F]{40}", h) or "@" in raw]
    long_hex = re.findall(r"[0-9a-f]{32,}", raw)
    check("%s holds no hash-like value" % path.name, not long_hex,
          "found %d long hex run(s)" % len(long_hex))

print("\n=== 3. the container-side file is ephemeral, not committed ===")
check("signup_counts.json is NOT tracked in git", not tracked("signup_counts.json"))
check("signup_counts.json is gitignored", ignored("signup_counts.json"))

print("\n=== 4. scanner_web.py ===")
web = (HERE / "scanner_web.py").read_text(encoding="utf-8")
check("defines the container-side counter file", "SIGNUP_COUNT_FILE" in web)
check("defines the committed baseline file", "SIGNUP_BASELINE_FILE" in web)
check("seeds the container counter from the committed total",
      "_signup_baseline_total" in web and "seed > total" in web)
check("exposes an aggregate count endpoint", "/api/signup-count" in web)
check("the endpoint returns only a total, not the list",
      '"total": _signup_total()' in web)
check("api_email_signup increments the counter", "_signup_increment()" in web)
# The increment must be conditional on the address being NEW. rfind, because
# the definition of _signup_increment comes first in the file and the CALL
# is the thing that has to be guarded.
inc = web.rfind("_signup_increment()")
pre = web[max(0, inc - 400):inc]
check("the increment only happens for a NEW address", "if not existing:" in pre,
      "the increment is not guarded by the new-address check")

print("\n=== 5. the funnel reads the durable number ===")
fun = (HERE / "measure_funnel.py").read_text(encoding="utf-8")
users = fun[fun.find("def link_users"):fun.find("def _stripe_counts")]
check("measure_funnel.py reads signup_baseline.json", "signup_baseline.json" in users)
# The precise thing is a REQUEST to the ephemeral export route. The path may
# appear in a comment explaining why it is not used.
check("it does NOT request the ephemeral address export",
      'http("/api/email-list-export")' not in users)
check("it falls back to the live aggregate endpoint", "/api/signup-count" in users)

print("\n=== 6. the sync is monotonic ===")
sync = HERE / "sync_signup_counter.py"
check("sync_signup_counter.py exists", sync.exists())
if sync.exists():
    s = sync.read_text(encoding="utf-8")
    check("it only ever moves the number UP", "max(cur, live)" in s)
    check("it writes the committed baseline", 'BASELINE.write_text' in s)
    check("it does not write addresses", "@" not in s.split('"note":')[-1].split('"total"')[0])

print("\n=== 7. the daily scan runs the sync ===")
ps1 = (HERE / "daily_scan.ps1").read_text(encoding="utf-8")
check("daily_scan.ps1 calls sync_signup_counter.py", "sync_signup_counter.py" in ps1)
check("a failed sync is non-fatal (an analytics counter must not take the site down)",
      "[SIGNUPS] WARN" in ps1)

print()
print("PASS %d / %d" % (len(passes), len(passes) + len(fails)))
if fails:
    print("FAILED - %d check(s):" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("ALL PASS")
sys.exit(0)
