#!/usr/bin/env python3
"""Refresh the durable signup counter AND ship it.

WHY A SEPARATE SCRIPT
---------------------
sync_signup_counter.py writes the tracked baseline. This one also commits and
pushes it, so the number actually reaches the deployed build.

WHY IT PUSHES
--------------
The counter lives on Railway's container disk and every redeploy destroys it.
The committed signup_baseline.json is what seeds the next boot, so a build
that does not carry a fresh count ships a stale one - and every push triggers
a deploy. Pushing the refreshed baseline is therefore the ONLY way the count
survives, and it has to be pushed, not merely committed locally: a local
commit is destroyed by the daily scan's hard reset and never reaches a build.

WHY IT ONLY PUSHES WHEN THE COUNT CHANGED
------------------------------------------
A push is a Railway build. Building hourly on a schedule would burn the plan's
build minutes to preserve a number that did not move. So it pushes only when
there is something new to preserve - which is exactly when the number would
otherwise be at risk.

Run:  python sync_and_push_signups.py
Exit 0 = nothing to do, or the refresh was shipped. Exit 1 = the counter could
not be read (never fatal to a deploy - this script is only ever run by hand
or by the hourly task).
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GIT = r"C:\Program Files\Git\cmd\git.exe"

# Files the scanner rewrites routinely. They are frequently dirty between
# scans and are NOT another lane's work in progress, so they must not stop
# this from shipping the count.
RUNTIME_FILES = {
    "ipo_etf_data.json", "pick_tracker.json", "scanner_data.json",
    "ai_earnings_today.html", "drip_status.json", "visitor_counts.json",
    "signup_counts.json", "funnel_history.json", "visitor_baseline.json",
}


def other_lane_wip():
    """True if a tracked file outside the runtime set is modified.

    A push is a deploy. Deploying another lane's half-finished work because
    a counter ticked over would be a much worse outcome than letting the
    count wait for the next commit - and the pre-commit hook already covers
    every commit, so waiting costs almost nothing.
    """
    st = git("status", "--porcelain")
    for line in (st.stdout or "").splitlines():
        if not line.strip() or line.startswith("??"):
            continue
        path = line[3:].strip().strip('"').replace("\\", "/")
        if path in RUNTIME_FILES:
            continue
        return path
    return None


def git(*args):
    return subprocess.run([GIT] + list(args), cwd=str(HERE),
                          capture_output=True, text=True, errors="replace")


def read_total():
    p = HERE / "signup_baseline.json"
    try:
        return int(json.loads(p.read_text(encoding="utf-8")).get("total", 0) or 0)
    except Exception:
        return 0


def main():
    before = read_total()
    r = subprocess.run([sys.executable, str(HERE / "sync_signup_counter.py")],
                       cwd=str(HERE), capture_output=True, text=True)
    if r.returncode != 0:
        print("[signups] counter could not be read - nothing shipped")
        print((r.stdout or r.stderr or "").strip()[:200])
        return 1
    after = read_total()
    if after == before:
        print("[signups] count unchanged at %d - nothing to ship" % after)
        return 0

    wip = other_lane_wip()
    if wip:
        print("[signups] not shipping - %s has uncommitted changes." % wip)
        print("[signups] A push is a deploy, and deploying another lane's")
        print("[signups] work in progress is worse than waiting for the next")
        print("[signups] commit - the pre-commit hook carries the count then.")
        return 0

    behind = git("rev-list", "--left-right", "--count", "origin/master...master").stdout.split()
    if len(behind) == 2 and behind[0] not in ("0", ""):
        print("[signups] not shipping - local is %s behind origin/master" % behind[0])
        return 0

    git("add", "signup_baseline.json")
    c = git("commit", "-m",
            "Signup count: %d -> %d\n\nThe free-signup counter lives on Railway's container disk and a "
            "redeploy destroys it. The committed signup_baseline.json is what seeds the next boot, "
            "so shipping the refreshed number is what makes the count survive a deploy. "
            "Aggregate only - no addresses, no hashes." % (before, after))
    if c.returncode != 0:
        print("[signups] commit failed: %s" % (c.stdout or c.stderr).strip()[:200])
        return 1
    p = git("push", "origin", "master")
    if p.returncode != 0:
        print("[signups] push failed: %s" % (p.stdout or p.stderr).strip()[:200])
        return 1
    print("[signups] shipped count %d -> %d" % (before, after))
    return 0


if __name__ == "__main__":
    sys.exit(main())
