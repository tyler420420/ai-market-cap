#!/usr/bin/env python3
"""Pull the live aggregate signup count into the git-tracked baseline.

WHY THIS EXISTS
---------------
Free signups were captured into email_list.json on Railway's container disk
and destroyed on every redeploy, and the only way to count them was the
export route, which needs a token that was never set. So the funnel's `users`
link read UNKNOWN - which reads identically to "nobody is signing up" and
attracts completely the wrong fix.

scanner_web.py now keeps a PII-free aggregate counter on the container and
seeds it at boot from signup_baseline.json, which IS committed. This script
reads the live absolute total and writes it back into that committed file, so
the number survives the next redeploy.

WHY IT IS AN ABSOLUTE TOTAL AND NOT baseline + window
----------------------------------------------------
sync_visitor_baseline.py writes the live all_time back as the baseline without
resetting the window, so all_time = baseline + hits double counts the window
on every sync. An absolute total has no window, so there is nothing to double
count. That is also why this file is written as a plain total and not as a
delta.

It only ever moves UP. A bad read, a partial response, or a redeploy landing
mid-read can never make the count go backwards.

Run:  python sync_signup_counter.py
Exit 0 = baseline written or already current. Exit 1 = could not read live.
"""

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASELINE = HERE / "signup_baseline.json"
LIVE = "https://aismarketcap.com/api/signup-count"


def read_live():
    req = urllib.request.Request(LIVE, headers={"User-Agent": "signup-counter-sync/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def main():
    try:
        d = read_live()
        live = int(d.get("total", 0) or 0)
    except Exception as e:
        print(f"[signups] could not read live counter: {e}")
        return 1

    cur = 0
    if BASELINE.exists():
        try:
            cur = int(json.loads(BASELINE.read_text(encoding="utf-8")).get("total", 0) or 0)
        except Exception:
            cur = 0

    new = max(cur, live)
    if new == cur:
        print(f"[signups] baseline already current at {cur}")
        return 0

    BASELINE.write_text(json.dumps({
        "total": new,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "note": ("Absolute total of free email signups captured. AGGREGATE ONLY - "
                 "no addresses, and no hashes of addresses (a salted SHA-256 of an "
                 "email is still brute-forceable, so it stays out of the repo too). "
                 "This file is committed and shipped with the code; Railway wipes "
                 "its container filesystem on every redeploy, so the container-side "
                 "counter seeds itself from this number at boot. That is what makes "
                 "the count survive a redeploy. Monotonic - it only ever moves up."),
    }, indent=2), encoding="utf-8")
    print(f"[signups] baseline {cur} -> {new} (live was {live})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
