#!/usr/bin/env python3
"""The signup counter must actually survive a redeploy, and keep doing so.

WHY THIS EXISTS
---------------
The counter lives on Railway's container disk. A redeploy replaces the
container, so the count restarts from whatever the committed
signup_baseline.json says. That makes the counter only as durable as the
sync interval - and with a once-a-day sync, any redeploy destroys up to a
day of captured signups.

The mechanism that actually fixes it is the PRE-COMMIT hook: it refreshes the
baseline before the commit is created, so every commit carries a fresh count
and therefore every push-triggered deploy ships one.

A pre-push hook cannot do this. A commit created inside a pre-push hook is
NOT pushed - git resolves the ref list before the hook runs - so the refreshed
count would sit locally and never reach a build. That was verified, not
assumed.

WHAT IS ASSERTED
1. .githooks/pre-commit refreshes the baseline, and does so BEFORE the hook's
   early exit - after that exit the refresh would never run for most commits.
2. The INSTALLED .git/hooks/pre-commit matches the tracked source byte for
   byte. A drifted hook is a guard that no longer guards.
3. The hourly task exists and points at the shipping script.
4. The refresh is monotonic - an absolute total, never baseline + hits.
"""
import hashlib
import io
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

fails = []
passes = []


def check(name, ok, detail=""):
    (passes if ok else fails).append(name)
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name,
                           ("   -- " + detail) if (detail and not ok) else ""))


def tracked(rel):
    return subprocess.run(["git", "-C", str(HERE), "ls-files", "--error-unmatch", rel],
                          capture_output=True, text=True).returncode == 0


print("=== 1. the tracked pre-commit hook refreshes the counter ===")
SRC = HERE / ".githooks" / "pre-commit"
check(".githooks/pre-commit exists", SRC.exists())
check(".githooks/pre-commit is tracked in git", tracked(".githooks/pre-commit"))
if SRC.exists():
    hook = SRC.read_text(encoding="utf-8", errors="replace")
    check("it calls sync_signup_counter.py", "sync_signup_counter.py" in hook)
    check("it stages the refreshed baseline", "add signup_baseline.json" in hook)
    # THE ORDER MATTERS. The hook exits early when nothing scanner-related is
    # staged, so a refresh placed after that exit would silently never run.
    sync_at = hook.find("sync_signup_counter.py")
    early_exit = hook.find("*ai_earnings_today.html*)")
    check("the refresh runs BEFORE the hook's early exit",
          sync_at != -1 and early_exit != -1 and sync_at < early_exit,
          "sync at %d, early exit at %d" % (sync_at, early_exit))
    # Scope to the refresh block itself. The route guard further down the
    # file legitimately does `exit 1` - that is not this block blocking a
    # commit, and a window that wide would fail for the wrong reason.
    blk_start = hook.find("# ---- refresh the durable signup counter")
    blk_end = hook.find("\n\n", blk_start) if blk_start != -1 else -1
    block = hook[blk_start:blk_end] if (blk_start != -1 and blk_end != -1) else ""
    check("the refresh block cannot block a commit", block and "exit 1" not in block,
          "the refresh block contains an exit 1")

print("\n=== 2. the installed hook matches the tracked source ===")
INST = HERE / ".git" / "hooks" / "pre-commit"
check(".git/hooks/pre-commit is installed", INST.exists())
if SRC.exists() and INST.exists():
    a = hashlib.sha256(SRC.read_bytes()).hexdigest()
    b = hashlib.sha256(INST.read_bytes()).hexdigest()
    check("installed hook is byte-identical to the tracked source", a == b,
          "tracked=%s installed=%s" % (a[:12], b[:12]))
check("install_hooks.ps1 exists", (HERE / "install_hooks.ps1").exists())

print("\n=== 3. the hourly shipping script and its task ===")
SHIP = HERE / "sync_and_push_signups.py"
check("sync_and_push_signups.py exists", SHIP.exists())
check("it is tracked in git", tracked("sync_and_push_signups.py"))
if SHIP.exists():
    s = SHIP.read_text(encoding="utf-8")
    check("it commits the refreshed baseline", 'git("add", "signup_baseline.json")' in s)
    check("it pushes", '"push", "origin", "master"' in s)
    check("it refuses to push another lane's work in progress",
          "other_lane_wip" in s)
    check("it only ships when the count actually moved", "after == before" in s)

q = subprocess.run(["schtasks", "/query", "/tn", "AISignupCounter", "/fo", "LIST", "/v"],
                   capture_output=True, text=True, errors="replace")
check("the AISignupCounter scheduled task exists", q.returncode == 0,
      (q.stdout or q.stderr or "").strip()[:120])
if q.returncode == 0:
    out = q.stdout
    check("it runs sync_and_push_signups.py", "sync_and_push_signups.py" in out)
    check("it is scheduled hourly",
          re.search(r"Schedule Type:.*Hourly", out, re.I) is not None
          or re.search(r"Repeat: Every:.*Hour", out, re.I) is not None,
          "schedule is not hourly")
    check("it is enabled", re.search(r"Scheduled Task State:\s*Enabled", out, re.I) is not None)

print("\n=== 4. the refresh is monotonic, never baseline + window ===")
sync = HERE / "sync_signup_counter.py"
check("sync_signup_counter.py exists", sync.exists())
if sync.exists():
    s = sync.read_text(encoding="utf-8")
    check("it only ever moves the number UP", "max(cur, live)" in s)
    check("it writes an absolute total, not a baseline offset",
          '"total": new' in s and '"since_boot"' not in s)
web = (HERE / "scanner_web.py").read_text(encoding="utf-8")
check("the container seeds from the committed absolute total",
      "seed = _signup_baseline_total()" in web and "seed > total" in web,
      "the seed is not read from the committed baseline")
# Scope to the SIGNUP block. The visitor counter still uses baseline + hits -
# that is a separate, separately-tracked commitment, and asserting it either
# way here would freeze a known-bad pattern in place.
seg_start = web.find("# ===== DURABLE AGGREGATE SIGNUP COUNTER")
seg = web[seg_start:seg_start + 6000] if seg_start != -1 else ""
check("the signup counter is not a baseline + window sum",
      seg and '"all_time": baseline + hits' not in seg,
      "the signup block sums a baseline and a window")

print()
print("PASS %d / %d" % (len(passes), len(passes) + len(fails)))
if fails:
    print("FAILED - %d check(s):" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("ALL PASS")
sys.exit(0)
