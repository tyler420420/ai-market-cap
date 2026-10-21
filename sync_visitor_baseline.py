#!/usr/bin/env python3
"""
Roll the live visitor count into the git-tracked baseline.

WHY THIS EXISTS
---------------
Railway redeploys wipe the container's filesystem. The live counter in
scanner_web.py (visitor_counts.json) therefore resets to 0 on every deploy, and
if all-time is computed as baseline + live, an unwritten baseline means the
public number snaps back to near zero each time CTO pushes.

This script reads the live count and writes the highest total ever observed
into visitor_baseline.json, which IS committed. Because it only ever moves the
number up, running it often or rarely is safe, and a temporary bad read can
never make the count go backwards.

Run:  python sync_visitor_baseline.py
Exit 0 = baseline written or already current. Exit 1 = could not read live.
"""

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASELINE = HERE / "visitor_baseline.json"
LIVE = "https://aismarketcap.com/api/visitors"


def read_live():
    req = urllib.request.Request(LIVE, headers={"User-Agent": "visitor-baseline-sync/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def main():
    try:
        d = read_live()
        live = int(d.get("all_time", 0) or 0)
    except Exception as e:
        print(f"[visitors] could not read live counter: {e}")
        return 1

    cur = 0
    if BASELINE.exists():
        try:
            cur = int(json.loads(BASELINE.read_text(encoding="utf-8")).get("all_time", 0) or 0)
        except Exception:
            cur = 0

    # Never write a lower value. A redeploy mid-read, or a partial response,
    # must not be able to roll the all-time total back.
    new = max(cur, live)
    if new == cur:
        print(f"[visitors] baseline already current at {cur}")
        return 0

    BASELINE.write_text(json.dumps({
        "all_time": new,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "note": ("All-time human page-view floor. Railway wipes its filesystem on "
                 "redeploy, so visitor_counts.json resets each deploy; this file is "
                 "committed and carries the total forward. Monotonic. "
                 "Aggregates only - no IPs stored."),
    }, indent=2), encoding="utf-8")
    print(f"[visitors] baseline {cur} -> {new} (live was {live})")
    return 0


if __name__ == "__main__":
    sys.exit(main())