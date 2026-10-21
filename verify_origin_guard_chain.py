"""Check the guard chain AS IT EXISTS ON ORIGIN/MASTER - not in this checkout.

verify_scan_deps.py checks the working tree. That is the wrong tree: the whole
question is whether a FRESH CLONE gets a complete guard chain. This resolves
each referenced guard through git's own object store at origin/master, so it
answers the question that actually matters after a push.

Read-only.
"""
import re
import subprocess

REPO = r"C:\Users\Tyler_AI\ai-market-cap"


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args],
                          capture_output=True, text=True).stdout


ps1 = git("show", "origin/master:daily_scan.ps1")

refs = sorted(set(re.findall(r"Join-Path \$repo '([^']+)'", ps1)))
guard_refs = [f for f in refs
              if f.startswith(("verify_", "prove_", "mutation_", "audit_"))]

print(f"=== guards daily_scan.ps1 references ON ORIGIN ({len(guard_refs)}) ===\n")

missing = []
for f in guard_refs:
    res = subprocess.run(["git", "-C", REPO, "cat-file", "-e",
                          f"origin/master:{f}"],
                         capture_output=True, text=True)
    present = res.returncode == 0
    print(f"  {'PRESENT' if present else 'ABSENT ':8} {f}")
    if not present:
        missing.append(f)

print("\n=== full guard inventory on origin (tracked guards) ===")
tracked = [g for g in git("ls-tree", "-r", "origin/master", "--name-only").split("\n")
           if g.startswith(("verify_", "prove_", "mutation_", "audit_"))]
for g in sorted(tracked):
    print(f"  {g}")

print("\n=== result ===")
if missing:
    print(f"DANGLING on origin - referenced but absent: {missing}")
    raise SystemExit(1)
print("PASSED - every guard daily_scan.ps1 runs is present on origin/master")