"""Prove verify_auth.py actually bites.

A guard that has never been seen to fail is an assumption, not a control. This
harness reinstates each original defect into a THROWAWAY COPY of scanner_web.py
and asserts the guard rejects it. The real repo file is never modified.

Run:  python prove_auth_guard_bites.py
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
GUARD = os.path.join(HERE, "verify_auth.py")

# scanner_web.py imports sibling modules that live in this repo. The harness
# runs it in a throwaway directory, so anything it imports must be staged there
# too - otherwise the baseline dies on ModuleNotFoundError and every mutation
# result becomes meaningless. Discovered, not hardcoded, so adding another
# module cannot silently break this harness again.
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
    shutil.copy(GUARD, os.path.join(workdir, "verify_auth.py"))
    for dep in sorted(_LOCAL_IMPORTS):
        shutil.copy(os.path.join(HERE, dep), os.path.join(workdir, dep))
    return sorted(_LOCAL_IMPORTS)

PY = sys.executable

# Each mutation: (name, old_substring, new_substring)
# Each must reintroduce a real historical defect.
MUTATIONS = [
    (
        "CRITICAL: /login grants Pro from a bare email again",
        # Reinstate the old GET-based login: email lookup alone sets the cookie.
        '    # GET — show the form. Any ?email= just prefills the input.\n'
        '    return _login_page((request.args.get(\'email\') or \'\').strip())',
        '    # GET — show the form. Any ?email= just prefills the input.\n'
        '    email_param = (request.args.get(\'email\') or \'\').strip()\n'
        '    cid, sub = get_customer_by_email(email_param)\n'
        '    if cid:\n'
        '        r = make_response(redirect("/", code=302))\n'
        '        r.set_cookie("stripe_customer", cid, max_age=86400*30,\n'
        '                     httponly=True, samesite=\'Lax\')\n'
        '        return r\n'
        '    return _login_page(email_param)',
    ),
    (
        # The faithful version of the original bug: reinstate the fail-open
        # branch that trusted an unsigned body. An earlier version of this
        # mutation only neutered the `if`, which still left signature
        # verification running and correctly rejected the payload - so it never
        # actually reproduced the vulnerability, and a guard that only checked
        # "state unchanged" passed on it. A mutation must recreate the DEFECT,
        # not merely a change.
        "HIGH: webhook trusts unsigned bodies again",
        '    if not STRIPE_WEBHOOK_SECRET:\n'
        '        print("[Webhook] FATAL: STRIPE_WEBHOOK_SECRET is not set - refusing to "\n'
        '              "process unsigned events. Set it in Railway to the signing secret "\n'
        '              "from Stripe Dashboard > Developers > Webhooks > your endpoint.")\n'
        '        return ("Webhook misconfigured: STRIPE_WEBHOOK_SECRET is not set on the "\n'
        '                "server. Unsigned events are rejected."), 500',
        '    if STRIPE_WEBHOOK_SECRET:\n'
        '        try:\n'
        '            event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)\n'
        '        except Exception as e:\n'
        '            return f"Webhook signature error: {e}", 400\n'
        '    else:\n'
        '        try:\n'
        '            event = json.loads(payload)\n'
        '        except Exception as e:\n'
        '            return f"JSON parse error: {e}", 400',
    ),
    (
        "LOW: a second weak is_subscriber() definition returns",
        'def is_subscriber():',
        'def is_subscriber():\n'
        '    """Weak duplicate - trusts cookie + local file only."""\n'
        '    cid = request.cookies.get("stripe_customer", "")\n'
        '    return bool(cid) and get_subscriptions().get(cid, {}).get("status") == "active"\n'
        '\n'
        '\n'
        'def is_subscriber_real():',
    ),
]

# The third mutation renames the real function; map the call sites back so the
# module still imports and the duplicate is genuinely live.
CALL_SITE_FIXUPS = [
    (re.compile(r'\bis_subscriber\(\)'), 'is_subscriber_real()'),
]


def run_guard(workdir):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run([PY, os.path.join(workdir, "verify_auth.py")],
                          cwd=workdir, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env,
                          timeout=300)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main():
    original = open(SRC, encoding="utf-8").read()

    # Sanity: the unmutated guard must pass, else a failing mutation proves nothing.
    base_dir = tempfile.mkdtemp(prefix="authbite_base_")
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
        workdir = tempfile.mkdtemp(prefix="authbite_")
        try:
            mutated = original.replace(old, new, 1)
            if name.startswith("LOW"):
                for pat, rep in CALL_SITE_FIXUPS:
                    mutated = pat.sub(rep, mutated)
            if mutated == original:
                print(f"[SKIP] {name}\n       mutation did not apply - "
                      f"anchor text not found. The guard for this defect may be "
                      f"stale.")
                all_caught = False
                continue
            deps = stage(workdir)
            open(os.path.join(workdir, "scanner_web.py"), "w",
                 encoding="utf-8").write(mutated)

            code, out = run_guard(workdir)
            caught = code != 0
            all_caught = all_caught and caught
            status = "CAUGHT" if caught else "MISSED"
            print(f"[{status}] {name}")
            if caught:
                # Show which check fired, so we know it failed for the right reason.
                for line in out.splitlines():
                    if line.strip().startswith("FAIL") or "auth invariants" in line \
                       or "FAILED -" in line:
                        print(f"          {line.strip()}")
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