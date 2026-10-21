#!/usr/bin/env python3
"""
LIVE PAYMENT-PATH GUARD - asserts the deployed site can actually take money.

THE INCIDENT THIS EXISTS FOR (2026-10-21)

Tyler's fix for the StripeObject crash and the "never strand a paying customer"
flow landed as commit 0f992ae. Every local suite was green: 41/41 activation
checks, 4/4 mutations caught. Then a real customer hit the live site and got
told "Payment received but there was a problem activating your account" -
for a session he had NOT paid. The code was correct. The DEPLOY was stale.

That is the signature failure of this entire project: the source is right and
the artifact is old, and no source-level test can see it. So this script tests
the artifact, over HTTP, against the live domain.

THE THREE CHECKS

  1. /success must not lie.
     Asked about a session that was never paid, the page must say something
     honest ("Almost there", "couldn't verify", "no payment"). It must NEVER
     say "Payment received". That sentence is the whole defect.

  2. /api/visitors must answer 200 with the full JSON shape.
     This endpoint was introduced in ef2fe16 and does not exist in older
     builds. It is therefore a deploy-FRESHNESS probe: 200 + correct keys
     means a recent build is serving; 404 means the deploy predates it. This
     replaces a one-off curl someone has to remember to run.

  3. /create-checkout must still redirect to Stripe.
     The claim "the buy path works" should be a machine check, not a belief.
     Both monthly and annual must 302 to checkout.stripe.com.

WHY /success IS PROBED WITH A FAKE SESSION

A well-formed but nonexistent session id is the ideal probe. It cannot belong
to anyone, cannot touch a real customer's record, and every version of this
code has to answer it one way or another:
  - pre-0f992ae build: crashes -> tells the visitor "Payment received"  <- BUG
  - 0f992ae+ build:       says "Almost there" / couldn't verify         <- OK
So the probe is safe, deterministic, and free of side effects.

FAILS CLOSED. Exit 1 on any failure. It never treats a network error as a pass.

    python verify_payment_live.py

prove_verify_payment_live_bites.py proves these assertions actually fail against
the pre-0f992ae wording. A check nobody has watched fail is an assumption.
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

BASE = "https://aismarketcap.com"
TIMEOUT = 30
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) site-audit"

# Probing /create-checkout over HTTP mints a real Stripe checkout session.
# Flask runs the view for HEAD too and only strips the body, so HEAD is NOT a
# way to avoid this - verified, not assumed. Rate limiting is the only thing
# that actually reduces it. One probe per hour caps churn at ~2 sessions/day
# instead of ~4 per scan, and daily_scan runs twice a day.
CHECKOUT_CACHE_TTL = 3600
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          ".checkout_probe_cache.json")

# Well-formed shape, guaranteed not to exist, and within Stripe's 66-char limit.
#
# LENGTH MATTERS, learned the hard way. An earlier probe id ran past 66 chars,
# so stripe.checkout.Session.retrieve rejected it outright ("Invalid string:
# must be at most 66 characters"). The old build's except branch then rendered
# the same "Payment received but there was a problem" apology - so the probe
# still saw the lie, but for a reason that had nothing to do with the defect it
# was meant to expose. One run also briefly showed that check PASSING, which
# was just that transient path, not progress.
#
# A probe that triggers a validation error is testing Stripe's input validation
# instead of our code. This one is well-formed and nonexistent, so every build
# takes its real path: the old build tries to activate a session that does not
# exist and says so, the fixed build verifies and reports honestly.
BOGUS_SESSION = "cs_live_" + "0" * 30 + "NONEXISTENTPROBE000000"

# The sentence that must NEVER appear on an unpaid session. This is the exact
# wording of the old build. Substring match, case-insensitive, so a cosmetic
# rewording of the same lie is still caught.
LIE_MARKERS = [
    "payment received but there was a problem",
    "payment received",
]

# Honest responses the fixed build may use instead.
HONEST_MARKERS = [
    "almost there",
    "couldn't verify",
    "could not verify",
    "couldn't find that payment",
    "no payment",
    "not able to verify",
    "unable to verify",
]

failures = []
warnings = []


def _load_checkout_cache():
    try:
        with open(CACHE_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _save_checkout_cache(data):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
    except Exception:
        pass  # caching is an optimisation; never fail the check over it


def _cache_age_seconds(cache):
    stamps = [v.get("at") for v in cache.values() if isinstance(v, dict)]
    if not stamps:
        return None
    return time.time() - min(stamps)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Stop at the 302 so we can inspect the redirect target itself."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_no_redirect = urllib.request.build_opener(_NoRedirect)


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}"
          + (f"   -- {detail}" if detail else ""))
    if not ok:
        failures.append(f"{name}: {detail}")
    return ok


def warn(name, detail=""):
    print(f"  WARN  {name}" + (f"   -- {detail}" if detail else ""))
    warnings.append(name)


def classify_success_page(body):
    """Return (is_lie, is_honest, title) for a /success response body."""
    low = body.lower()
    is_lie = any(m in low for m in LIE_MARKERS)
    is_honest = any(m in low for m in HONEST_MARKERS)
    m = re.search(r"<title>(.*?)</title>", body, re.S | re.I)
    title = m.group(1).strip() if m else "(no <title>)"
    return is_lie, is_honest, title


def main():
    print("=" * 66)
    print("LIVE PAYMENT-PATH GUARD")
    print(f"target: {BASE}")
    print("=" * 66)

    # ---------- 1. /success must not lie about an unpaid session ----------
    print("\n=== 1. /success must not claim payment for an unpaid session ===")
    try:
        req = urllib.request.Request(
            f"{BASE}/success?session_id={BOGUS_SESSION}", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read().decode("utf-8", "replace")
            status = r.status
        is_lie, is_honest, title = classify_success_page(body)
        check("/success responds 200", status == 200, f"got {status}")
        check("/success does NOT say 'Payment received' for an unpaid session",
              not is_lie,
              f"page title={title!r} - this is the OLD pre-0f992ae build")
        check("/success tells the truth about an unpaid session",
              is_honest,
              f"page title={title!r} - expected honest wording "
              f"(looked for: {', '.join(HONEST_MARKERS[:4])})")
        if is_lie:
            print()
            print("  *** DEPLOY IS STALE. The live build predates 0f992ae. ***")
            print("  *** A paying customer is being told their payment was")
            print("  *** received when it may not have been at all.          ***")
    except urllib.error.HTTPError as e:
        check("/success responds 200", False, f"HTTP {e.code}")
    except Exception as e:
        # A network failure is NOT a pass. Fail closed.
        check("/success is reachable", False,
              f"{type(e).__name__}: {str(e)[:80]}")

    # ---------- 2. deploy freshness via /api/visitors ----------
    print("\n=== 2. deploy freshness: /api/visitors ===")
    print("  (introduced in ef2fe16; 404 means the deploy predates it)")
    visitors_ok = False
    try:
        req = urllib.request.Request(f"{BASE}/api/visitors",
                                     headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read().decode("utf-8", "replace")
            status = r.status
        if status == 200:
            try:
                data = json.loads(raw)
            except Exception:
                data = {}
            required = ["all_time", "baseline", "since_boot", "today",
                        "today_hits", "last7"]
            missing = [k for k in required if k not in data]
            check("/api/visitors -> 200", True)
            check("/api/visitors returns the expected JSON shape",
                  not missing, f"missing keys: {missing}")
            if not missing:
                print(f"         all_time={data['all_time']} "
                      f"today={data['today']} last7={data['last7']}")
                print("         -> deploy freshness: CURRENT (recent build serving)")
                visitors_ok = True
        else:
            check("/api/visitors -> 200", False, f"got {status}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            check("/api/visitors -> 200", False,
                  "404 - live deploy PREDATES this endpoint (stale build)")
        else:
            check("/api/visitors -> 200", False, f"HTTP {e.code}")
    except Exception as e:
        check("/api/visitors is reachable", False,
              f"{type(e).__name__}: {str(e)[:80]}")

    if not visitors_ok:
        print("         -> deploy freshness: STALE (cannot confirm current build)")

    # ---------- 3. the buy path still works ----------
    # SIDE-EFFECT WARNING - LEARNED THE HARD WAY
    # The obvious fix for the session-churn problem is to use HEAD instead of
    # GET. That DOES NOT WORK. Flask routes a HEAD request to the view function
    # exactly like a GET and only strips the response BODY afterwards, so
    # stripe.checkout.Session.create still executes and still mints a session.
    # This was verified, not assumed: the HEAD responses below carry fresh
    # cs_live_ ids on every run. Anyone who "fixes" this with HEAD and assumes
    # the churn stopped will keep creating ~4 sessions a day forever.
    #
    # So the real mitigation is RATE LIMITING, below: probe the live buy path
    # at most once per hour and serve the cached verdict in between.
    #
    # HONEST LIMIT: this proves a customer can REACH Stripe checkout. It does
    # not prove a payment COMPLETES. An invalid-but-present Stripe key, or a
    # deleted price id, only fails when a real payment is attempted, and that
    # cannot be synthesized without charging a real card. Necessary, not
    # sufficient; a completed payment remains the only full proof.
    print("\n=== 3. /create-checkout must redirect to Stripe (cached 1h) ===")
    cache = _load_checkout_cache()
    age = _cache_age_seconds(cache)
    if cache and age < CHECKOUT_CACHE_TTL:
        print(f"         (cached {int(age)}s ago - not re-probing to avoid "
              f"creating Stripe sessions)")
        for plan in ("monthly", "annual"):
            entry = cache.get(plan) or {}
            check(f"/create-checkout?plan={plan} redirects to Stripe checkout",
                  bool(entry.get("ok")),
                  f"cached verdict: {entry.get('detail', '(none)')}")
    else:
        fresh = {}
        for plan in ("monthly", "annual"):
            try:
                req = urllib.request.Request(
                    f"{BASE}/create-checkout?plan={plan}",
                    headers={"User-Agent": UA})
                try:
                    r = _no_redirect.open(req, timeout=TIMEOUT)
                    status, loc = r.status, r.headers.get("Location", "")
                except urllib.error.HTTPError as e:
                    status, loc = e.code, e.headers.get("Location", "")
                ok = (status in (301, 302, 303, 307, 308)
                      and "checkout.stripe.com" in loc)
                detail = f"HTTP {status} -> {loc[:60] or '(no Location header)'}"
                check(f"/create-checkout?plan={plan} redirects to Stripe checkout",
                      ok, detail)
                fresh[plan] = {"ok": bool(ok), "detail": detail,
                               "at": int(time.time())}
            except Exception as e:
                detail = f"{type(e).__name__}: {str(e)[:60]}"
                check(f"/create-checkout?plan={plan} redirects to Stripe checkout",
                      False, detail)
                fresh[plan] = {"ok": False, "detail": detail,
                               "at": int(time.time())}
        _save_checkout_cache(fresh)

    # /pricing must offer both plans, so the buy entry points actually exist.
    try:
        req = urllib.request.Request(f"{BASE}/pricing", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            pricing = r.read().decode("utf-8", "replace")
        has_monthly = "/create-checkout?plan=monthly" in pricing
        has_annual = "/create-checkout?plan=annual" in pricing
        check("/pricing offers the monthly checkout link", has_monthly)
        check("/pricing offers the annual checkout link", has_annual)
    except Exception as e:
        check("/pricing is reachable", False, f"{type(e).__name__}: {str(e)[:80]}")

    # ---------- result ----------
    print("\n" + "=" * 66)
    if failures:
        print(f"FAILED - {len(failures)} check(s) failed. The live payment path")
        print("is NOT in the state the source says it should be.")
        for f in failures:
            print(f"  - {f}")
        print("=" * 66)
        return 1
    print("PASSED - the live payment path matches the current source.")
    if warnings:
        print(f"({len(warnings)} warning(s))")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    sys.exit(main())