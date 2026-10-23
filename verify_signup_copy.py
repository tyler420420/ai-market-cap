#!/usr/bin/env python3
"""The STATIC signup block must not promise a delivery that cannot happen.

WHY THIS EXISTS
---------------
The signup form's headline and subhead promised a daily email unconditionally
("This is the one email that tells you what to trade each morning before the
open"). EMAIL_EXPORT_TOKEN was unset, so not one address could ever become a
delivered email.

The honest text - SIGNUP_MSG_NOT_READY - existed, but only in the POST
RESPONSE. A visitor who never signs up never sees it. So the promise was all
most people ever read, and the truth only reached the people who had already
converted. A page that over-promises and then apologises after the signup is
worse than a page that never promised.

So the block itself is now rendered from the same _delivery_ready() gate the
POST response uses. This guard asserts BOTH directions, because a guard that
only checks the not-ready state would still pass if the code always rendered
the honest copy - including after the token lands and the promise becomes
true.

It imports scanner_web and calls the real _email_capture() with the token
flipped both ways. No network, no live site, no side effects.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

fails = []
passes = []


def check(name, ok, detail=""):
    (passes if ok else fails).append(name)
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name,
                           ("   -- " + detail) if (detail and not ok) else ""))


# The promise that must NOT appear while delivery is impossible.
PROMISE = "tells you what to trade each morning before the open"
PROMISE_HEAD = "Get tomorrow's pick by email"
HONEST = "not switched on yet"

print("=== loading scanner_web ===")
try:
    import scanner_web as sw
except Exception as e:
    print("  FAIL  could not import scanner_web.py: %s" % e)
    print("\nFAILED - the module under test did not load, so nothing was proven.")
    sys.exit(1)
print("  PASS  scanner_web imported")

print("\n=== the template carries no hardcoded promise ===")
tpl = sw.EMAIL_CAPTURE
check("EMAIL_CAPTURE has no literal promise sentence", PROMISE not in tpl)
check("EMAIL_CAPTURE has no literal promising headline", PROMISE_HEAD not in tpl)
check("EMAIL_CAPTURE is templated", "__PROMISE__" in tpl and "__HEADLINE__" in tpl)

print("\n=== delivery NOT ready (the state Railway is in right now) ===")
sw.EMAIL_EXPORT_TOKEN = ""
check("_delivery_ready() is False with no token", sw._delivery_ready() is False)
not_ready = sw._email_capture()
check("the rendered block does NOT promise a daily email", PROMISE not in not_ready,
      "the promise is still in the static copy")
check("the rendered block does NOT use the promising headline",
      PROMISE_HEAD not in not_ready)
check("the rendered block says plainly it is not switched on", HONEST in not_ready)
check("no unsubstituted token is left in the markup",
      "__PROMISE__" not in not_ready and "__HEADLINE__" not in not_ready
      and "__BUTTON__" not in not_ready)
check("the button does not say 'Send it to me'",
      "Send it to me" not in not_ready)

print("\n=== delivery ready (the state after Tyler pastes the token) ===")
sw.EMAIL_EXPORT_TOKEN = "test-token-not-a-real-secret"
check("_delivery_ready() is True with a token", sw._delivery_ready() is True)
ready = sw._email_capture()
check("the rendered block DOES promise a daily email", PROMISE in ready)
check("the rendered block uses the promising headline", PROMISE_HEAD in ready)
check("the button says 'Send it to me'", "Send it to me" in ready)
check("no unsubstituted token is left in the markup",
      "__PROMISE__" not in ready and "__HEADLINE__" not in ready
      and "__BUTTON__" not in ready)

print("\n=== the page actually serves the rendered block ===")
web = (HERE / "scanner_web.py").read_text(encoding="utf-8")
check("the page splices _email_capture(), not the raw template",
      "'<body>' + _email_capture()" in web)
check("the raw template is not spliced directly",
      "'<body>' + EMAIL_CAPTURE" not in web)

print()
print("PASS %d / %d" % (len(passes), len(passes) + len(fails)))
if fails:
    print("FAILED - %d check(s):" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("ALL PASS")
sys.exit(0)
