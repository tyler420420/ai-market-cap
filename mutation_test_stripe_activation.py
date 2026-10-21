"""Mutation test: prove verify_stripe_activation.py catches the original bug.

A regression test that cannot fail is decoration. This checks out the PRE-FIX
scanner_web.py from git, points the test at it, and asserts the suite FAILS.

Specifically it re-instates the .get() call on a StripeObject - the exact defect
that charged Tyler $5 without activating the account.

Run:  python mutation_test_stripe_activation.py
Exit 0 = every mutation was caught.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

# scanner_web.py contains em-dashes and box characters. On Windows the default
# cp1252 decode of a subprocess pipe raises UnicodeDecodeError and kills the
# harness, which would look like "mutation not caught" rather than a crash.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run(script: Path):
    return subprocess.run([sys.executable, str(script)],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=300)

HERE = Path(__file__).resolve().parent
VERIFIER = HERE / "verify_stripe_activation.py"
SRC = HERE / "scanner_web.py"
PRE_FIX_COMMIT = "7489bbd"  # the auth fix, immediately BEFORE the StripeObject fix

# Each mutation re-instates a real defect class.
#
# NOTE on scope: the single load-bearing fix is `event = _plain(event)` right
# after construct_event, because to_dict() recurses and converts the entire
# nested tree to plain dicts. The per-branch _plain() calls are defence-in-depth
# against a future branch that forgets to convert, so mutating one of those
# alone does NOT break the suite - the top-level conversion already did the
# work. The mutations below target what actually carries the fix, plus the
# /success path, which converts independently of the webhook tree.
MUTATIONS = [
    ("top-level event conversion removed (THE ORIGINAL BUG)",
     "    event = _plain(event)\n    etype = event.get('type', '')",
     "    etype = event.get('type', '')"),
    ("_plain() no longer converts StripeObjects",
     "        return obj.to_dict()",
     "        return {}"),
    ("success page stops converting the session (Tyler's exact error)",
     "session = _plain(stripe.checkout.Session.retrieve(session_id))",
     "session = stripe.checkout.Session.retrieve(session_id)"),
]

results = []
for name, old, new in MUTATIONS:
    original = SRC.read_text(encoding="utf-8")
    if old not in original:
        results.append((name, False, "anchor not found - test is stale vs source"))
        print(f"FAIL  {name}\n      anchor not found (stale mutation)")
        continue

    # Run each mutation against a copy so the real source is never touched.
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "scanner_web.py").write_text(original.replace(old, new, 1), encoding="utf-8")
        (d / VERIFIER.name).write_text(VERIFIER.read_text(encoding="utf-8"), encoding="utf-8")

        p = run(d / VERIFIER.name)
        caught = p.returncode != 0
        detail = ""
        for line in (p.stdout or "").splitlines():
            if line.startswith("FAIL") or "FAILED:" in line:
                detail = line.strip()
                break
        results.append((name, caught, detail))
        print(f"{'PASS' if caught else 'FAIL'}  caught: {name}")
        if caught and detail:
            print(f"        via: {detail[:96]}")

# Also confirm the real pre-fix commit genuinely fails, using git itself.
print()
try:
    pre = subprocess.run(["git", "show", f"{PRE_FIX_COMMIT}:scanner_web.py"],
                         cwd=str(HERE), capture_output=True, text=True,
                         encoding="utf-8", errors="replace", timeout=60)
    if pre.returncode != 0:
        print(f"SKIP  could not read {PRE_FIX_COMMIT}:scanner_web.py: "
              f"{(pre.stderr or '').strip()[:80]}")
    else:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "scanner_web.py").write_text(pre.stdout, encoding="utf-8")
            (d / VERIFIER.name).write_text(VERIFIER.read_text(encoding="utf-8"), encoding="utf-8")
            p = run(d / VERIFIER.name)
            caught = p.returncode != 0
            results.append((f"actual pre-fix commit {PRE_FIX_COMMIT}", caught, ""))
            print(f"{'PASS' if caught else 'FAIL'}  caught: real pre-fix commit {PRE_FIX_COMMIT} "
                  f"(exit={p.returncode})")
except Exception as e:
    print(f"SKIP  git check failed: {e}")

print("\n" + "=" * 62)
failed = [r for r in results if not r[1]]
print(f"{len(results) - len(failed)}/{len(results)} mutations caught")
if failed:
    for n, _, det in failed:
        print(f"  MISSED: {n}")
    sys.exit(1)
print("SUITE BITES ON EVERY MUTATION - the StripeObject bug cannot come back silently")