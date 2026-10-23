"""Prove verify_subscriber_gate.py actually bites.

A guard that has never been seen to fail is an assumption, not a control. This
harness reinstates each original subscriber-gate defect into a THROWAWAY COPY
of scanner_web.py and asserts the guard rejects it. The real repo file is never
modified.

Run:  python prove_subscriber_gate_bites.py
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "scanner_web.py")
GUARD = os.path.join(HERE, "verify_subscriber_gate.py")

_LOCAL_IMPORTS = set()
try:
    _body = io.open(SRC, encoding="utf-8").read()
except Exception:
    _body = ""
for _m in re.finditer(r"^\s*(?:import\s+(\w+)|from\s+(\w+)\s+import)", _body, re.M):
    _mod = _m.group(1) or _m.group(2)
    if _mod and os.path.exists(os.path.join(HERE, _mod + ".py")):
        _LOCAL_IMPORTS.add(_mod + ".py")


def stage(workdir):
    """Copy everything the guard needs to import scanner_web.py in isolation."""
    shutil.copy(SRC, os.path.join(workdir, "scanner_web.py"))
    shutil.copy(GUARD, os.path.join(workdir, "verify_subscriber_gate.py"))
    for dep in sorted(_LOCAL_IMPORTS):
        shutil.copy(os.path.join(HERE, dep), os.path.join(workdir, dep))
    # The guard's data-integrity section reads subscriptions.json next to itself.
    # The behavioural sections build their OWN fixtures in throwaway dirs, but
    # this one deliberately reads the real committed file - so it has to be
    # staged or the guard reports "subscriptions.json exists / file not found"
    # and the baseline fails for a reason that has nothing to do with the
    # mutation under test.
    subs = os.path.join(HERE, "subscriptions.json")
    if os.path.exists(subs):
        shutil.copy(subs, os.path.join(workdir, "subscriptions.json"))
    return sorted(_LOCAL_IMPORTS)


PY = sys.executable

MUTATIONS = [
    (
        # THE redeploy bug, verbatim. This short-circuit is what silently revoked
        # every paid account on every Railway redeploy: the container disk came
        # back empty, the record was "missing", and missing meant False.
        "CRITICAL: missing local record short-circuits to False again "
        "(redeploy revokes every payer)",
        "    local = subs.get(customer_id, {})\n"
        "    local_status = local.get('status')\n"
        "    if local_status == 'active':\n"
        "        return True\n",
        "    local = subs.get(customer_id, {})\n"
        "    local_status = local.get('status')\n"
        "    if local_status == 'active':\n"
        "        return True\n"
        "    if not local:\n"
        "        return False\n",
    ),
    (
        # The other historical defect: a weak duplicate of the check that trusts
        # the cookie alone. Any visitor who sets stripe_customer=anything would
        # be waved through.
        "CRITICAL: cookie-only gate lets any visitor in",
        "def is_subscriber():\n"
        '    """Check if current visitor has an active subscription.',
        "def is_subscriber():\n"
        '    """Weak duplicate - trusts the cookie alone."""\n'
        "    return bool(request.cookies.get('stripe_customer', ''))\n"
        "\n"
        "\n"
        "def is_subscriber_real():\n"
        '    """Check if current visitor has an active subscription.',
    ),
    (
        # Fail-OPEN instead of fail-closed: if the Stripe key is missing, grant
        # access rather than deny it. Nothing in the matrix catches this by
        # value alone, so it is pinned explicitly here.
        "HIGH: missing Stripe key fails OPEN instead of denying",
        "    if not stripe.api_key:\n"
        "        return False\n"
        "    return _stripe_validate_active(customer_id)",
        "    if not stripe.api_key:\n"
        "        return True\n"
        "    return _stripe_validate_active(customer_id)",
    ),
]

# The second mutation renames the real function; map call sites back so the
# module still imports and the weak duplicate is genuinely live.
CALL_SITE_FIXUPS = [
    (re.compile(r'\bis_subscriber\(\)'), 'is_subscriber_real()'),
]


def run_guard(workdir):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run([PY, os.path.join(workdir, "verify_subscriber_gate.py")],
                          cwd=workdir, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env,
                          timeout=600)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main():
    original = io.open(SRC, encoding="utf-8").read()

    # Sanity: the unmutated guard must pass, else a caught mutation proves nothing.
    base_dir = tempfile.mkdtemp(prefix="subgate_base_")
    deps = stage(base_dir)
    print(f"[baseline] staged local deps: {deps or '(none)'}")
    code, out = run_guard(base_dir)
    print(f"[baseline] unmutated guard exit={code}")
    if code != 0:
        print(out[-3000:])
        print("\nBASELINE FAILED - the guard does not pass on clean code, so a "
              "mutation 'caught' would be meaningless.")
        return 1
    print("[baseline] PASS - clean code is accepted\n")

    all_caught = True
    for name, old, new in MUTATIONS:
        workdir = tempfile.mkdtemp(prefix="subgate_mut_")
        try:
            mutated = original.replace(old, new, 1)
            if name.startswith("CRITICAL: cookie-only"):
                for pat, rep in CALL_SITE_FIXUPS:
                    mutated = pat.sub(rep, mutated)
            if mutated == original:
                print(f"[SKIP] {name}\n       mutation did not apply - anchor text "
                      f"not found. The guard for this defect may be stale.")
                all_caught = False
                continue
            stage(workdir)
            with io.open(os.path.join(workdir, "scanner_web.py"), "w",
                         encoding="utf-8") as f:
                f.write(mutated)

            code, out = run_guard(workdir)
            caught = code != 0
            all_caught = all_caught and caught
            print(f"[{'CAUGHT' if caught else 'MISSED'}] {name}")
            if caught:
                for line in out.splitlines():
                    s = line.strip()
                    if s.startswith("FAIL"):
                        print(f"          {s}")
            else:
                print("          guard returned 0 on known-bad code")
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    shutil.rmtree(base_dir, ignore_errors=True)

    print("\n=== result ===")
    if all_caught:
        print(f"PASSED - all {len(MUTATIONS)} injected defects were caught")
        return 0
    print("FAILED - at least one injected defect slipped through. The guard is "
          "not trustworthy.")
    return 1


if __name__ == "__main__":
    sys.exit(main())