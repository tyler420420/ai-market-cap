"""Cross-check: every file daily_scan.ps1 references must be TRACKED in git.

The 2026-10-21 incident class: a script stages the artifact it produces but not
the generator that produces it, so a fresh clone renders a placeholder forever.
fetch_ipo_etf.py was missing from the add list while ipo_etf_data.json was
staged. verify_payment_live.py was referenced by daily_scan.ps1 but never
committed at all.

This finds that class of miss mechanically instead of by eye.
"""
import re
import subprocess
import sys

REPO = r"C:\Users\Tyler_AI\ai-market-cap"
PS1 = "daily_scan.ps1"

body = open(f"{REPO}\\{PS1}", encoding="utf-8").read()
refs = sorted(set(re.findall(r"Join-Path \$repo '([^']+)'", body)))

# Files that are runtime scratch, not sources - absence is expected.
EXPECTED_UNTRACKED = {
    "daily_scan.log",       # rotating log
    ".scan.lock",           # lock file
    "scan_guard_skip.txt",  # marker, written by the script itself
    "live_stale_deploy.txt",  # marker, written by the script itself
}

tracked = set(subprocess.run(
    ["git", "-C", REPO, "ls-files"],
    capture_output=True, text=True).stdout.split("\n"))

# A referenced file that is GITIGNORED is legitimate and expected: that is what
# ignoring a file means. alert.env holds ALERT_API_KEY and .alert_sent_today.txt
# is a daily marker - both are local state, and the old rule ("referenced implies
# tracked") pushed whoever hit it toward `git add alert.env`, i.e. toward
# committing a credential to satisfy a guard. Ignore is the correct outcome.
# git check-ignore answers for a pathname whether or not it exists on disk.
# Enumerating ignored files with `ls-files --others --ignored` cannot: a marker
# that has not been written yet is simply not there to be listed, and the one
# file most likely to be correctly absent would read as untracked-and-broken.
def is_ignored(f):
    return subprocess.run(["git", "-C", REPO, "check-ignore", "-q", f]).returncode == 0

print(f"=== files daily_scan.ps1 references ({len(refs)}) ===")
problems = []
for f in refs:
    is_tracked = f in tracked
    is_ignored_now = is_ignored(f)
    exists = __import__("os").path.exists(f"{REPO}\\{f}")
    note = ""
    if not is_tracked and not is_ignored and f not in EXPECTED_UNTRACKED:
        problems.append(f)
        note = "  <-- UNTRACKED, not ignored, and referenced"
    elif not is_tracked and is_ignored:
        note = "  (expected: gitignored - local secrets or runtime state)"
    elif not is_tracked:
        note = "  (expected: runtime scratch)"
    elif not exists:
        note = "  <-- TRACKED but MISSING from this checkout"
    print(f"  tracked={str(is_tracked):<5} exists={str(exists):<5} {f}{note}")

print("\n=== also check the files it stages ===")
add_lines = re.findall(r"& \$git add ([^\r\n]+)", body)
staged = " ".join(add_lines).replace("`", " ")
staged_files = [s for s in staged.split() if "." in s]
for f in staged_files:
    mark = "" if f in tracked else "  <-- STAGED BUT NOT TRACKED?!"
    print(f"  {'tracked' if f in tracked else 'UNTRACKED':<9} {f}{mark}")

print("\n=== result ===")
if problems:
    print(f"FAILED - {len(problems)} referenced file(s) are not tracked:")
    for p in problems:
        print(f"  - {p}")
    sys.exit(1)
print("PASSED - everything daily_scan.ps1 depends on is tracked in git")