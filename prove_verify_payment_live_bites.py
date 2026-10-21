"""Prove verify_payment_live.py actually fails on the old build's wording.

verify_auth.py already paid for this lesson once: it accepted ANY error code
for the webhook, so a mutation returning 400 instead of 500 passed, and the
guard shipped with a hole. A green guard proves nothing until someone has
watched it go red on the exact defect it exists to catch.

So this serves the pre-0f992ae /success wording (the real "Payment received
but there was a problem activating your account" apology) plus a stale-build
/api/visitors, and asserts the guard's classifier calls it a LIE and a STALE
deploy - not a pass.

It does NOT hit the live site. Everything is local.
"""
import sys
import os
import re as _re
import ast as _ast
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "vpl", os.path.join(HERE, "verify_payment_live.py"))
vpl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vpl)

# The EXACT body the old build returned for an unpaid session.
OLD_BUILD_SUCCESS_PAGE = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Payment Problem</title></head><body>
<h1>Payment received but there was a problem activating your account</h1>
<p>Please email support@aismarketcap.com with your receipt.
Error: 'StripeObject' object has no attribute 'get'</p>
</body></html>"""

# A correct fix, in the wording 0f992ae actually shipped.
NEW_BUILD_SUCCESS_PAGE = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Almost there - AI Market Cap</title></head>
<body><h1>Almost there</h1>
<p>We couldn't verify that payment. Your card was not charged again.</p>
<a href=/account>Go to your account</a></body></html>"""

# A build that is neither honest nor dishonest - must still not be a pass.
AMBIGUOUS_PAGE = "<html><body><h1>OK</h1></body></html>"

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   -- {detail}" if detail else ""))


print("=== the OLD build's unpaid-session wording must be flagged as a LIE ===")
is_lie, is_honest, title = vpl.classify_success_page(OLD_BUILD_SUCCESS_PAGE)
check("old wording detected as LIE", is_lie, f"title={title!r}")
check("old wording NOT accepted as honest", not is_honest,
      "an apology that says 'payment received' is not honesty")

print("\n=== the NEW build's wording must be accepted ===")
is_lie2, is_honest2, title2 = vpl.classify_success_page(NEW_BUILD_SUCCESS_PAGE)
check("new wording NOT flagged as a lie", not is_lie2, f"title={title2!r}")
check("new wording detected as honest", is_honest2, f"title={title2!r}")

print("\n=== an ambiguous page must not silently pass ===")
# This is the important one: a page that is neither must be REJECTED, because
# 'if it does not say the lie, it must be fine' is exactly the false-pass
# assumption that produced the verify_auth.py hole.
is_lie3, is_honest3, _ = vpl.classify_success_page(AMBIGUOUS_PAGE)
check("ambiguous page is neither lie nor honest", not is_lie3 and not is_honest3,
      "so it cannot satisfy the honesty assertion")

print("\n=== a cosmetic rewording of the same lie is still caught ===")
# "We received your payment" means the same lie. Substring coverage must hold.
REWORDED = "<html><body><h1>Payment Received</h1></body></html>"
is_lie4, _, _ = vpl.classify_success_page(REWORDED)
check("reworded lie still detected", is_lie4)

print("\n=== /api/visitors freshness marker ===")
# The marker endpoint only exists in newer builds, so a 404 must be a FAILURE
# and never a warning-and-carry-on. Staleness that only warns is staleness that
# ships.
check("visitors freshness keys are declared",
      all(k in vpl.__dict__ for k in ("BASE", "BOGUS_SESSION", "LIE_MARKERS")))
check("the probe session id is well-formed",
      vpl.BOGUS_SESSION.startswith("cs_live_") and len(vpl.BOGUS_SESSION) > 30,
      "must look like a real checkout session so the old code takes its "
      "normal path and reveals the lie")
check("the probe session id is obviously fake",
      "NONEXISTENTPROBE" in vpl.BOGUS_SESSION,
      "cannot collide with a real customer's session")
# Stripe rejects checkout session ids longer than 66 characters. An earlier
# probe id ran to 110 chars, so Session.retrieve threw a validation error and
# the OLD build rendered its apology through that error path - the probe was
# exercising Stripe's input validation, not the code it meant to test. It even
# produced one run where the lie check spuriously PASSED, which is how a probe
# bug can masquerade as a deployment.
check("probe session id is within Stripe's 66-char limit",
      len(vpl.BOGUS_SESSION) <= 66,
      f"len={len(vpl.BOGUS_SESSION)}; over-length ids fail validation before "
      f"reaching our code")

print("\n=== checkout probe must not mint real Stripe sessions every run ===")
# This guard runs twice a day from daily_scan.ps1. Probing /create-checkout
# over HTTP really does call Session.create.
#
# The obvious fix is HEAD instead of GET. THAT DOES NOT WORK - Flask runs the
# view function for HEAD and only strips the body, so the session is still
# created. This was verified against the live site: HEAD responses carried fresh
# cs_live_ ids on every run. So the assertion below requires CACHING, and
# separately pins the fact that the file does NOT claim HEAD is sufficient.
src = open(os.path.join(HERE, "verify_payment_live.py"), encoding="utf-8").read()
src_flat = " ".join(_re.sub(r"#", " ", src.lower()).split())

check("checkout probe is rate limited (cache TTL declared)",
      "CHECKOUT_CACHE_TTL" in src,
      "HTTP-probing /create-checkout mints a real Stripe session every time")
check("cache is consulted before re-probing",
      "_load_checkout_cache" in src and "if cache and age < CHECKOUT_CACHE_TTL" in src)

# STRUCTURAL, not substring. An earlier version of this check merely asserted
# the phrase 'cached verdict' appeared somewhere in the file - which stays true
# if the cached value is accepted without being checked, and also matches an
# unrelated comment. A guard that passes on the defect it exists to catch is
# worse than no guard. Parse the file and confirm a check(...) call actually
# inspects the cached entry.
try:
    tree = _ast.parse(src)
    cached_asserted = False
    for node in _ast.walk(tree):
        if not isinstance(node, _ast.Call):
            continue
        fn = node
        name = getattr(getattr(fn, "func", None), "id", None)
        if name != "check":
            continue
        blob = " ".join(_ast.dump(a) for a in node.args)
        # a check() whose arguments reference the cached entry's "ok" value
        if "entry" in blob and "ok" in blob:
            cached_asserted = True
            break
except Exception as e:
    cached_asserted = False
    print(f"         (AST parse failed: {e})")
check("cached verdict is ASSERTED, not silently trusted",
      cached_asserted,
      "must be a real check() call reading the cached ok value, so a stale "
      "pass cannot hide")

print("\n=== the HEAD trap is documented, not repeated ===")
# If someone later 'optimises' this back to HEAD believing it avoids the
# session, the file should already explain why that is wrong. Require the
# specific correction, not a vague gesture at the topic.
# Require the SPECIFIC mechanism, not a generic "does not work". A loose
# 'or' fallback matched a phrase that survived the mutation - deleting the
# first half of the note left enough behind to still satisfy it, and the
# regression slipped through. Pin the claim that makes the trap unambiguous.
head_trap = "head request to the view function" in src_flat
check("guard explains that HEAD does NOT avoid session creation",
      head_trap,
      "must name the mechanism (Flask runs the view for HEAD and only strips "
      "the body), not just assert that HEAD fails somehow")
check("guard is explicit that the buy path cannot be fully proven",
      "cannot be proven" in src_flat or "cannot be synthesized" in src_flat,
      "necessary but not sufficient must be stated plainly")

print("\n=== result ===")
failed = [n for n, ok, _ in results if not ok]
if failed:
    print(f"FAILED - {len(failed)} of {len(results)} checks failed:")
    for n in failed:
        print(f"  - {n}")
    sys.exit(1)
print(f"PASSED - {len(results)}/{len(results)} checks confirm the live guard "
      f"catches the old build's lie")