"""Prove the HEAD-not-GET regression check actually fails.

12/12 green is only meaningful if the new assertions can go red. This mutates
the guard source in a throwaway copy - reverting it to the session-creating GET
and stripping the honest-limit caveat - and asserts the bite test catches both.
A mutation must recreate the DEFECT, not merely a change.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "verify_payment_live.py")
BITE = os.path.join(HERE, "prove_verify_payment_live_bites.py")
PY = sys.executable

original = open(SRC, encoding="utf-8").read()

MUTATIONS = [
    (
        # The original defect: no rate limiting, so every run mints Stripe
        # sessions. Restores the un-mitigated behaviour.
        "checkout rate limiting removed",
        "    if cache and age < CHECKOUT_CACHE_TTL:",
        "    if False and cache and age < CHECKOUT_CACHE_TTL:",
    ),
    (
        # The subtler one: cache is consulted, but the cached verdict is
        # accepted without being checked. A stale PASS would then be served
        # forever and the buy path could rot unnoticed.
        # Anchor uses the real 12-space indent of the cached branch.
        "cached verdict trusted without being asserted",
        '            check(f"/create-checkout?plan={plan} redirects to Stripe checkout",\n'
        '                  bool(entry.get("ok")),\n'
        '                  f"cached verdict: {entry.get(\'detail\', \'(none)\')}")',
        '            _ = entry  # trust the cache blindly',
    ),
    (
        # Strip the whole note, INCLUDING the line carrying the distinctive
        # mechanism claim. An earlier mutation deleted only the first line of
        # the two-line sentence, left enough behind to satisfy a loose 'or'
        # fallback, and the regression slipped through silently.
        "HEAD trap note deleted",
        "    # GET. That DOES NOT WORK. Flask routes a HEAD request to the view function\n"
        "    # exactly like a GET and only strips the response BODY afterwards, so\n"
        "    # stripe.checkout.Session.create still executes and still mints a session.",
        "    # (note removed)",
    ),
]

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   -- {detail}" if detail else ""))


def run_bite(workdir):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run([PY, os.path.join(workdir, "prove_verify_payment_live_bites.py")],
                       cwd=workdir, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, timeout=300)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


# Baseline: unmutated must pass, else a caught mutation proves nothing.
base = tempfile.mkdtemp(prefix="paybite_base_")
shutil.copy(SRC, os.path.join(base, "verify_payment_live.py"))
shutil.copy(BITE, os.path.join(base, "prove_verify_payment_live_bites.py"))
code, out = run_bite(base)
print(f"[baseline] unmutated bite test exit={code}")
if code != 0:
    print(out[-2500:])
    print("\nBASELINE FAILED - the bite test does not pass on clean code.")
    sys.exit(1)
print("[baseline] PASS\n")
shutil.rmtree(base, ignore_errors=True)

all_caught = True
for name, old, new in MUTATIONS:
    wd = tempfile.mkdtemp(prefix="paybite_")
    try:
        mutated = original.replace(old, new, 1)
        if mutated == original:
            print(f"[SKIP] {name}\n       anchor not found - assertion may be stale")
            all_caught = False
            continue
        open(os.path.join(wd, "verify_payment_live.py"), "w",
             encoding="utf-8").write(mutated)
        shutil.copy(BITE, os.path.join(wd, "prove_verify_payment_live_bites.py"))
        code, out = run_bite(wd)
        caught = code != 0
        all_caught = all_caught and caught
        print(f"[{'CAUGHT' if caught else 'MISSED'}] {name}")
        if caught:
            for line in out.splitlines():
                if line.strip().startswith("FAIL") or "checks failed" in line:
                    print("          ", line.strip())
        else:
            print("           bite test still passed on mutated source")
    finally:
        shutil.rmtree(wd, ignore_errors=True)

print("\n=== result ===")
if all_caught:
    print(f"PASSED - all {len(MUTATIONS)} regressions are caught")
    sys.exit(0)
print("FAILED - a regression slipped through")
sys.exit(1)