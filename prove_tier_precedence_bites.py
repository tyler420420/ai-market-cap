"""Prove the tier-precedence guard rejects the reverted (first-wins) code.

WHY THIS EXISTS
A guard that passes against correct code proves only that the code is correct
today. It does not prove the guard would CATCH the regression, which is the
only thing that matters when the whole class of bug is a silent wrong email
to a paying customer. A guard that cannot fail is decoration.

So: restore the old first-wins dedup, require the guard to fail, then restore
the fix and require it to pass. The file is backed up first and restored from
that backup in a finally block, so an exception mid-run cannot leave the
repo holding the bug.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
SRC = SITE / "send_daily_alert.py"
GUARD = SITE / "verify_email_list.py"
PY = sys.executable

FIXED_DEDUP = '''    seen = {}
    for e, paid in out:
        k = e.lower().strip()
        if not k:
            continue
        if k not in seen or paid:
            seen[k] = (k, paid)
    return list(seen.values())'''

OLD_DEDUP = '''    seen, uniq = set(), []
    for e, paid in out:
        k = e.lower().strip()
        if k and k not in seen:
            seen.add(k)
            uniq.append((k, paid))
    return uniq'''


def run_guard():
    p = subprocess.run([PY, "-X", "utf8", str(GUARD)],
                       capture_output=True, text=True, cwd=str(SITE))
    return p.returncode, p.stdout + p.stderr


def main():
    backup = Path(tempfile.mkdtemp()) / SRC.name
    shutil.copy2(SRC, backup)
    original = SRC.read_text(encoding="utf-8")
    failures = []
    try:
        if FIXED_DEDUP not in original:
            print("SETUP FAIL: the fixed dedup block was not found in the source")
            return 1
        print("CONTROL  guard against the FIXED code ...", end=" ", flush=True)
        code, out = run_guard()
        ok = code == 0
        print("PASS" if ok else "FAIL rc=%s" % code)
        if not ok:
            failures.append("the guard fails against correct code")

        print("MUTANT   reverting to first-wins dedup ...", end=" ", flush=True)
        SRC.write_text(original.replace(FIXED_DEDUP, OLD_DEDUP), encoding="utf-8")
        code, out = run_guard()
        caught = code != 0
        tier_lines = [l.strip() for l in out.splitlines()
                      if "both lists" in l or "collision" in l or "PAID email" in l]
        print("CAUGHT (rc=%s)" % code if caught else "ESCAPED (rc=%s)" % code)
        for l in tier_lines:
            print("      " + l)
        if not caught:
            failures.append("first-wins dedup ESCAPED the guard - it tests nothing")
    finally:
        shutil.copy2(backup, SRC)
        restored = SRC.read_text(encoding="utf-8")
        assert restored == original, "RESTORE FAILED - repo left mutated!"
        shutil.rmtree(backup.parent, ignore_errors=True)

    print("\nRESTORED source matches the pre-test bytes: %s"
          % (restored == original))
    print("\n=== %s ===" % ("MUTATION CAUGHT" if not failures
                           else "; ".join(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())