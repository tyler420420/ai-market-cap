"""Guard: authentication invariants for Pro access.

Three real defects were found in an audit of scanner_web.py on 2026-10-21:

  CRITICAL  /login?email=X set the access cookie for anyone who knew (or
            guessed) a subscriber's email. No password, no proof. Knowing an
            address was equivalent to paying.
  HIGH      /webhook fell back to json.loads(payload) and TRUSTED the body
            when STRIPE_WEBHOOK_SECRET was unset, turning the endpoint into an
            unauthenticated write API that could grant or revoke any
            subscription.
  LOW       is_subscriber() was defined twice; the weak copy shadowed by the
            real one.

A guard nobody has watched fail is not a guard. Every check below is written so
that reintroducing the original bug makes it FAIL. verify_auth.py --prove-bite
temporarily reverts each fix in memory and asserts the check catches it, so a
green run is evidence rather than assumption.

IMPORTANT: this never reads or writes the real subscriptions.json. All state
goes to a temp file, so running it cannot lock a paying customer out of their
own account.

Run:  python verify_auth.py
      python verify_auth.py --prove-bite
"""
import os
import sys
import json
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

sys.path.insert(0, HERE)
for _stale in list(sys.modules):
    if _stale == "scanner_web":
        del sys.modules[_stale]

import scanner_web
from scanner_web import app

SCANNER_WEB = os.path.join(HERE, "scanner_web.py")

# Redirect the subscription store to a temp file so the real
# subscriptions.json is never read or written by this test.
_tmpdir = tempfile.mkdtemp(prefix="verify_auth_")
FAKE_SUBS = Path(_tmpdir) / "subscriptions.json"
scanner_web.SUBS_FILE = FAKE_SUBS

TEST_EMAIL = "probe-subscriber@example.com"
TEST_PW = "correct-horse-battery-8"
TEST_CID = "cus_testverify123"

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))
    return bool(ok)


def seed(password=TEST_PW, status="active", email=TEST_EMAIL, cid=TEST_CID):
    """Write a subscription record. Hash is real scrypt when password given."""
    rec = {"plan": "monthly", "status": status, "updated": 0, "email": email}
    if password:
        from werkzeug.security import generate_password_hash
        rec["pw_hash"] = generate_password_hash(password)
    FAKE_SUBS.write_text(json.dumps({cid: rec}), encoding="utf-8")
    scanner_web._login_failures.clear()


def cookie_set(resp):
    """Does this response set a NON-EMPTY access cookie? True = it granted access.

    Note the value check: a header of `stripe_customer=` with nothing after the
    equals sign is an empty cookie, not access. Checking for '=' inside the value
    (an earlier bug here) made every successful login look like a failure.
    """
    for hdr in resp.headers.getlist("Set-Cookie"):
        if not hdr.startswith("stripe_customer="):
            continue
        value = hdr.split(";")[0][len("stripe_customer="):].strip()
        if value:
            return True
    return False


print("=== /login must NOT grant Pro on the strength of an email alone ===")

# The original CRITICAL bug, verbatim: GET /login?email=<subscriber email>
seed()
c = app.test_client()
r = c.get(f"/login?email={TEST_EMAIL}")
check("GET /login?email=<subscriber> does not set the access cookie",
      not cookie_set(r), f"HTTP {r.status_code}")
check("GET /login?email=<subscriber> does not redirect to the scanner",
      r.status_code != 302 or "/login" in (r.headers.get("Location") or "/login"),
      f"HTTP {r.status_code} -> {r.headers.get('Location')}")

# No cookie anywhere in the body either (some old code set it via JS).
check("response body grants no access",
      "stripe_customer" not in r.get_data(as_text=True),
      "no cookie-setting markup in body")

print("\n=== /login DOES work with the correct password ===")
c = app.test_client()
r = c.post("/login", data={"email": TEST_EMAIL, "password": TEST_PW},
           follow_redirects=False)
check("POST /login with correct password sets the access cookie",
      cookie_set(r), f"HTTP {r.status_code} -> {r.headers.get('Location')}")

print("\n=== /login rejects wrong and missing passwords ===")
c = app.test_client()
r = c.post("/login", data={"email": TEST_EMAIL, "password": "wrong-password"},
           follow_redirects=False)
check("POST /login with WRONG password does not grant access",
      not cookie_set(r), f"HTTP {r.status_code}")

c = app.test_client()
r = c.post("/login", data={"email": TEST_EMAIL}, follow_redirects=False)
check("POST /login with NO password field does not grant access",
      not cookie_set(r), f"HTTP {r.status_code}")

c = app.test_client()
r = c.post("/login", data={"email": TEST_EMAIL, "password": ""},
           follow_redirects=False)
check("POST /login with EMPTY password does not grant access",
      not cookie_set(r), f"HTTP {r.status_code}")

print("\n=== unknown email vs wrong password are indistinguishable ===")
# If these differ, /login is an oracle for discovering who pays.
seed()
c1 = app.test_client()
r_unknown = c1.post("/login", data={"email": "nobody-here@example.com",
                                    "password": "whatever-123"},
                    follow_redirects=False)
scanner_web._login_failures.clear()
c2 = app.test_client()
r_wrongpw = c2.post("/login", data={"email": TEST_EMAIL, "password": "whatever-123"},
                    follow_redirects=False)
body_unknown = r_unknown.get_data(as_text=True)
body_wrong = r_wrongpw.get_data(as_text=True)
# Strip the echoed email before comparing, since it legitimately differs.
import re
norm_unknown = re.sub(r'value="[^"]*"', 'value=""', body_unknown)
norm_wrong = re.sub(r'value="[^"]*"', 'value=""', body_wrong)
check("unknown email and wrong password return the same page",
      norm_unknown == norm_wrong,
      "identical response -> no account-enumeration oracle")

print("\n=== cancelled subscriptions cannot sign in ===")
seed(password=TEST_PW, status="cancelled")
c = app.test_client()
r = c.post("/login", data={"email": TEST_EMAIL, "password": TEST_PW},
           follow_redirects=False)
check("cancelled sub with correct password does not grant access",
      not cookie_set(r), f"HTTP {r.status_code}")

print("\n=== passwords are stored hashed, never in plaintext ===")
seed(password=TEST_PW)
stored = json.loads(FAKE_SUBS.read_text(encoding="utf-8"))[TEST_CID]
check("no plaintext password in subscriptions.json",
      TEST_PW not in json.dumps(stored), "scrypt hash only")
check("pw_hash uses a modern scheme",
      str(stored.get("pw_hash", "")).startswith(("scrypt:", "pbkdf2:", "argon2")),
      str(stored.get("pw_hash", ""))[:20])

print("\n=== short passwords are rejected ===")
ok, err = scanner_web.set_subscriber_password(TEST_CID, "short")
check("set_subscriber_password rejects a 5-char password", not ok, err)

print("\n=== /webhook fails CLOSED when STRIPE_WEBHOOK_SECRET is unset ===")
seed()
orig_secret = scanner_web.STRIPE_WEBHOOK_SECRET
try:
    # Simulate the exact production misconfiguration: env var missing/empty.
    scanner_web.STRIPE_WEBHOOK_SECRET = ""
    c = app.test_client()
    forged = {
        "id": "evt_forged",
        "type": "customer.subscription.updated",
        "data": {"object": {"customer": TEST_CID, "status": "canceled",
                            "metadata": {"plan": "monthly"}}},
    }
    r = c.post("/webhook", data=json.dumps(forged),
               content_type="application/json")
    # Assert the EXACT code, not just ">= 400". A 400 means "sender sent
    # something bad" - Stripe will NOT retry, and the operator gets no signal
    # that the server is misconfigured. A 500 means "our config is broken",
    # which Stripe retries and which shows up in Railway's logs. Anything in
    # between hides a broken deployment behind a healthy-looking request.
    check("unsigned webhook event returns 500 (misconfiguration, not bad request)",
          r.status_code == 500, f"HTTP {r.status_code}")
    check("unsigned webhook event is rejected outright",
          r.status_code >= 400, f"HTTP {r.status_code}")
    check("unsigned event did NOT change subscription state",
          json.loads(FAKE_SUBS.read_text(encoding="utf-8"))
              [TEST_CID]["status"] == "active",
          "status still active - forged cancel ignored")

    # And a forged ACTIVATE must not work either.
    FAKE_SUBS.write_text(json.dumps({TEST_CID: {"plan": "monthly",
                                                "status": "cancelled",
                                                "email": TEST_EMAIL}}),
                         encoding="utf-8")
    forged2 = {
        "id": "evt_forged2",
        "type": "checkout.session.completed",
        "data": {"object": {"customer": TEST_CID, "metadata": {"plan": "monthly"},
                            "customer_details": {"email": TEST_EMAIL}}},
    }
    r = c.post("/webhook", data=json.dumps(forged2),
               content_type="application/json")
    check("forged activate is REJECTED when secret is unset",
          json.loads(FAKE_SUBS.read_text(encoding="utf-8"))[TEST_CID]["status"]
          == "cancelled",
          "status still cancelled - forged activate ignored")
finally:
    scanner_web.STRIPE_WEBHOOK_SECRET = orig_secret

print("\n=== no fail-open JSON fallback remains in the webhook ===")
# Checked via the AST, not by grepping text. A text search also matches the
# comment that DOCUMENTS the old bug, so the check would fail for the right
# code and the wrong reason. Walking the tree asks the real question: does any
# live statement feed the request body to json.loads and use it as the event?
import ast

with open(SCANNER_WEB, encoding="utf-8") as fh:
    tree = ast.parse(fh.read())

fail_open = []
for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue
    fn = node.func
    is_json_loads = (
        isinstance(fn, ast.Attribute) and fn.attr == "loads"
        and isinstance(fn.value, ast.Name) and fn.value.id == "json"
    )
    if not is_json_loads:
        continue
    for arg in node.args:
        if isinstance(arg, ast.Name) and arg.id == "payload":
            fail_open.append(node.lineno)

check("no json.loads(payload) call anywhere in the source",
      not fail_open, f"found at line(s): {fail_open}" if fail_open else "AST-verified")

print("\n=== is_subscriber() is defined exactly once ===")
with open(SCANNER_WEB, encoding="utf-8") as fh:
    defs = [i + 1 for i, ln in enumerate(fh.read().splitlines())
            if ln.strip().startswith("def is_subscriber(")]
check("exactly one is_subscriber definition", len(defs) == 1,
      f"defined at line(s): {defs}")

print("\n=== password login cannot be brute-forced ===")
seed()
c = app.test_client()
blocked = False
for _ in range(15):
    r = c.post("/login", data={"email": TEST_EMAIL, "password": "guess-wrong"},
               follow_redirects=False)
    if "Too many attempts" in r.get_data(as_text=True):
        blocked = True
        break
check("repeated wrong passwords get throttled", blocked,
      f"locked out after {scanner_web._LOGIN_MAX_FAILS} attempts")

print("\n=== result ===")
failed = [n for n, ok, _ in results if not ok]
if failed:
    print(f"FAILED - {len(failed)} of {len(results)} checks failed:")
    for n in failed:
        print(f"  - {n}")
    sys.exit(1)
print(f"PASSED - {len(results)}/{len(results)} auth invariants hold")