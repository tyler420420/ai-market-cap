"""Prove the subscriber gate actually opens for payers and stays shut for everyone else.

WHY THIS EXISTS

Tyler asked the only question that matters about a fresh deploy: does subscriber
data still work after the scan rebuilds everything?

The design answer is that Stripe is the source of truth and
subscriptions.json is only a cache, because subscriptions.json lives on
Railway's ephemeral container disk and comes back EMPTY after every deploy.
A paying customer whose cache vanished must therefore still get in, and a
random visitor must still get nothing.

Both halves are easy to break silently:

  * An earlier version of is_subscriber() short-circuited on a MISSING local
    record and returned False. Every paid account was silently revoked by a
    routine deploy, and the site kept working, so nothing looked broken.

  * A hand-rolled duplicate of the check once crept into a second route, which
    read only the cookie and the local file and never asked Stripe.

So this guard EXERCISES is_subscriber() with a stubbed Stripe rather than
reading its source. A grep cannot tell you the gate opens; only a call can.

It runs scanner_web.py from a THROWAWAY copy with a purpose-built
subscriptions.json, so the real repo file is never read for the behavioural
cases, never written, and no network call is ever made.

Run:  python verify_subscriber_gate.py
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "scanner_web.py")

FAILS = []
CHECKS = 0


def check(ok, label, detail=""):
    global CHECKS
    CHECKS += 1
    if ok:
        print(f"PASS  {label}")
    else:
        print(f"FAIL  {label}" + (f"\n      {detail}" if detail else ""))
        FAILS.append(label)


def note(label):
    print(f"NOTE  {label}")


def discover_local_imports():
    """scanner_web.py imports sibling modules that live in this repo. A throwaway
    copy cannot import them unless they are staged too. Discovered, never
    hardcoded, so adding another module cannot silently break this guard."""
    found = set()
    try:
        body = io.open(SRC, encoding="utf-8").read()
    except Exception:
        body = ""
    for m in re.finditer(r"^\s*(?:import\s+(\w+)|from\s+(\w+)\s+import)", body, re.M):
        mod = m.group(1) or m.group(2)
        if mod and os.path.exists(os.path.join(HERE, mod + ".py")):
            found.add(mod + ".py")
    return sorted(found)


def run_matrix(subs, cases, label):
    """Stage the app with a CONTROLLED subscriptions.json and run `cases`.

    Each case is [name, cookies, key_present, stripe_verdict, expected]:
      key_present      -> whether the server has STRIPE_SECRET_KEY in its env
      stripe_verdict True/False  -> _stripe_validate_active returns that
      stripe_verdict "NOT_CALLED" -> the stub records that it must never run

    key_present matters and is not cosmetic. scanner_web.py sets
    stripe.api_key straight from os.environ["STRIPE_SECRET_KEY"] with no file
    fallback, so `if not stripe.api_key: return False` is a real fork in
    production, not a theoretical one. Production has the key and asks Stripe.
    An instance that somehow lost it must DENY rather than hand out access it
    cannot verify, and this guard pins both branches so neither can drift.
    """
    workdir = tempfile.mkdtemp(prefix="subgate_")
    try:
        shutil.copy(SRC, os.path.join(workdir, "scanner_web.py"))
        for dep in discover_local_imports():
            shutil.copy(os.path.join(HERE, dep), os.path.join(workdir, dep))
        with io.open(os.path.join(workdir, "subscriptions.json"), "w",
                     encoding="utf-8") as f:
            f.write(json.dumps(subs))
        with io.open(os.path.join(workdir, "_cases.json"), "w",
                     encoding="utf-8") as f:
            f.write(json.dumps(cases))
        runner = os.path.join(workdir, "_run_matrix.py")
        with io.open(runner, "w", encoding="utf-8") as f:
            f.write(RUNNER_SRC)
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run([sys.executable, runner], cwd=workdir,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", env=env, timeout=300)
        out = (proc.stdout or "") + (proc.stderr or "")
        try:
            results = json.loads(out.split("__RESULT__", 1)[1].splitlines()[0])
        except Exception:
            check(False, f"[{label}] harness produced no parsable result",
                  (out.strip()[-1500:] or "(no output at all)"))
            return
        for r in results:
            if r.get("error"):
                check(False, f"[{label}] {r['name']}", r["error"])
            else:
                check(r["got"] == r["want"], f"[{label}] {r['name']}",
                      "" if r["got"] == r["want"]
                      else f"expected {r['want']!r}, got {r['got']!r}")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


RUNNER_SRC = r'''
import json
import scanner_web as sw

CASES = json.loads(open("_cases.json", encoding="utf-8").read())
out = []
for name, cookies, key_present, verdict, want in CASES:
    called = {"v": False}

    def stub(customer_id, _v=verdict, _c=called):
        _c["v"] = True
        return False if _v == "NOT_CALLED" else bool(_v)

    sw._stripe_validate_active = stub
    # scanner_web.py reads this from os.environ at import time with no file
    # fallback, so it has to be reassigned per case to model a server that has
    # the key and one that has lost it.
    sw.stripe.api_key = "sk_test_present" if key_present else ""
    cookie_hdr = "; ".join("%s=%s" % (k, v) for k, v in cookies.items())
    headers = {"Cookie": cookie_hdr} if cookie_hdr else {}
    try:
        with sw.app.test_request_context("/", headers=headers):
            got = sw.is_subscriber()
        # If the case demands Stripe NOT be consulted, prove it was not.
        if verdict == "NOT_CALLED" and called["v"]:
            got = "STRIPE_WAS_CALLED_UNEXPECTEDLY"
        out.append({"name": name, "got": got, "want": want})
    except Exception as e:
        out.append({"name": name, "error": "%s: %s" % (type(e).__name__, e)})
print("__RESULT__" + json.dumps(out))
'''


def main():
    # ================= 1. the gate, with a warm local cache =================
    warm_subs = {
        "cus_ACTIVE": {"plan": "monthly", "status": "active",
                       "email": "payer@example.com", "sub_id": "sub_1"},
        "cus_CANCELLED": {"plan": "monthly", "status": "cancelled",
                          "email": "gone@example.com"},
    }
    warm_cases = [
        # --- must stay SHUT ---
        ["no cookie at all is not a subscriber", {}, True, False, False],
        ["unknown customer id is not a subscriber",
         {"stripe_customer": "cus_DOES_NOT_EXIST"}, True, False, False],
        ["cancelled customer with a local record stays out",
         {"stripe_customer": "cus_CANCELLED"}, True, False, False],
        ["customer absent locally AND not active at Stripe stays out",
         {"stripe_customer": "cus_GONE"}, True, False, False],
        # --- must OPEN ---
        ["active local record opens the gate without asking Stripe",
         {"stripe_customer": "cus_ACTIVE"}, True, "NOT_CALLED", True],
    ]
    run_matrix(warm_subs, warm_cases, "warm cache")

    # ========== 2. THE REDEPLOY: container disk wiped, cache is empty ==========
    # This is what Railway actually does on every deploy. A payer must still get
    # in, which can only happen if is_subscriber() asks Stripe rather than
    # short-circuiting on the missing record.
    wipe_cases = [
        ["paying customer still gets in after the cache was wiped",
         {"stripe_customer": "cus_ACTIVE"}, True, True, True],
        ["cancelled-at-Stripe customer still stays out after a wipe",
         {"stripe_customer": "cus_CANCELLED"}, True, False, False],
        ["stranger still gets nothing after a wipe",
         {"stripe_customer": "cus_RANDOM"}, True, False, False],
        # --- the fail-closed branch: no key means no verification is possible,
        # so a wiped cache must DENY rather than guess. Granting access that
        # cannot be verified is how a deleted account keeps paying access.
        ["wiped cache + missing Stripe key denies instead of guessing",
         {"stripe_customer": "cus_ACTIVE"}, False, True, False],
    ]
    run_matrix({}, wipe_cases, "redeploy-wiped-cache")

    # ================= 3. the committed subscriber data =======================
    real = os.path.join(HERE, "subscriptions.json")
    try:
        data = json.loads(io.open(real, encoding="utf-8").read())
        check(isinstance(data, dict), "subscriptions.json parses as an object",
              "got %s" % type(data).__name__)
        actives = {k: v for k, v in data.items() if v.get("status") == "active"}
        check(len(actives) >= 1, "subscriptions.json has at least one active sub",
              "actives: %s" % sorted(actives))
        bad_email = [k for k, v in actives.items() if not v.get("email")]
        check(not bad_email,
              "every active record carries an email (needed for /login recovery "
              "and the paid alert)", "missing email: %s" % bad_email)
        # Two customer ids on ONE email is correct - that is one person holding
        # two subscriptions, not a duplicated row. Two records sharing ONE
        # sub_id would be corruption, because a Stripe subscription belongs to
        # exactly one customer.
        by_sub = {}
        for k, v in actives.items():
            if v.get("sub_id"):
                by_sub.setdefault(v["sub_id"], []).append(k)
        collide = {s: cs for s, cs in by_sub.items() if len(cs) > 1}
        check(not collide,
              "no Stripe sub_id is claimed by two customer records (that would "
              "be real corruption)", "collisions: %s" % collide)
        by_email = {}
        for k, v in actives.items():
            if v.get("email"):
                by_email.setdefault(v["email"].strip().lower(), []).append(k)
        multi = {e: cs for e, cs in by_email.items() if len(cs) > 1}
        for e, cs in multi.items():
            note("one email holds %d customer ids %s - multi-subscription payer, "
                 "expected; the mailer must collapse these to one recipient"
                 % (len(cs), sorted(cs)))
    except FileNotFoundError:
        check(False, "subscriptions.json exists", "file not found")
    except Exception as e:
        check(False, "subscriptions.json parses as an object",
              "%s: %s" % (type(e).__name__, e))

    print("\n=== %d/%d subscriber-gate checks passed ==="
          % (CHECKS - len(FAILS), CHECKS))
    if FAILS:
        print("FAILED:")
        for f_ in FAILS:
            print("  - " + f_)
        return 1
    print("PASSED - payers get in (including after a wiped cache), "
          "everyone else stays out")
    return 0


if __name__ == "__main__":
    sys.exit(main())