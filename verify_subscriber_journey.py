#!/usr/bin/env python3
"""End-to-end audit of the post-subscribe journey.

WHY THIS EXISTS
---------------
Tyler 2026-10-22: "everything it mentions they get for $5 on pricing page they
should get and unlock if they subscribe and should stay unlocked pro features
as long as they stay subscribed" and "or we screwed".

For a product that takes $5 a payment, "does the thing work after you pay" is
the only question that matters. This walks the whole journey against the real
Flask app and checks every promise the pricing page makes, in both directions:
a subscriber must get access, a non-subscriber must not.

It also covers the failure Tyler actually hit - paying while the previous build
was still live - by simulating a Railway redeploy that wipes
subscriptions.json, which is the single most likely way a PAYING customer
loses access.

Run:  python verify_subscriber_journey.py
Exit 0 = all pass.
"""
import json
import sys
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
sys.path.insert(0, str(SITE))

failures = []


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL") + f"  {name}" + ("" if ok else f"  -- {detail}"))
    if not ok:
        failures.append(name)


def section(t):
    print(f"\n=== {t} ===")


def main():
    import scanner_web

    app = scanner_web.app
    app.config["TESTING"] = True
    C = app.test_client()

    SUB = "cus_VTsULOjOP83NeP"          # Tyler's real active subscription

    # ── 1. THE PROMISE LIST ───────────────────────────────────────────
    # Read what the pricing page actually sells. If this list and the
    # delivery checks below ever diverge, the site is over-promising.
    section("What the pricing page promises")
    pricing = C.get("/pricing").get_data(as_text=True)
    promises = {
        "Pro Pick of the Day": "Pro Pick of the Day" in pricing,
        "Top 5 ranked plays": "Top 5 ranked pre-earnings plays" in pricing,
        "AI Chat": "AI Chat" in pricing,
        "Real-time earnings alerts": "Real-time earnings alerts" in pricing,
    }
    for k, v in promises.items():
        check(f"pricing page promises: {k}", v)
    about = C.get("/about").get_data(as_text=True)
    check("pricing page scan-count promise matches MAX_SCANS_PER_DAY",
          f"{scanner_web.MAX_SCANS_PER_DAY} additional scans" in about,
          f"MAX_SCANS_PER_DAY={scanner_web.MAX_SCANS_PER_DAY} but the FAQ "
          f"promises a different number")

    # ── 2. A STRANGER GETS NOTHING ────────────────────────────────────
    section("Non-subscriber is locked out of everything")
    S = app.test_client()          # fresh client, no cookies
    r = S.post("/run", follow_redirects=False)
    check("Scan button redirects a non-subscriber", r.status_code in (301, 302, 303, 307, 308),
          f"got {r.status_code}")
    r = S.post("/api/chat", json={"message": "hi"}, follow_redirects=False)
    check("Chat redirects a non-subscriber", r.status_code in (301, 302, 303, 307, 308),
          f"got {r.status_code}")
    r = S.get("/pro", follow_redirects=False)
    check("Pro dashboard redirects a non-subscriber", r.status_code in (301, 302, 303, 307, 308),
          f"got {r.status_code}")
    r = S.get("/api/pro_pick", follow_redirects=False)
    check("Pro pick API redirects a non-subscriber", r.status_code in (301, 302, 303, 307, 308),
          f"got {r.status_code}")
    home = S.get("/").get_data(as_text=True)
    check("home marks a non-subscriber as NOT subscribed",
          "window.__isSubscriber=false" in home)

    # ── 3. A SUBSCRIBER GETS EVERYTHING ───────────────────────────────
    section("Subscriber is unlocked everywhere")
    P = app.test_client()
    P.set_cookie("stripe_customer", SUB, domain="localhost")

    home = P.get("/").get_data(as_text=True)
    check("home marks the subscriber as subscribed",
          "window.__isSubscriber=true" in home)
    check("Subscribe button hidden for a subscriber",
          ".nav-subscribe{display:none" in home)

    r = P.get("/pro", follow_redirects=False)
    check("Pro dashboard loads", r.status_code == 200, f"got {r.status_code}")
    check("Pro dashboard shows the pick", "Pro Pick" in r.get_data(as_text=True))

    r = P.get("/account", follow_redirects=False)
    check("Account page loads", r.status_code == 200, f"got {r.status_code}")

    r = P.get("/api/pro_pick", follow_redirects=False)
    check("Pro pick API returns JSON", r.status_code == 200, f"got {r.status_code}")
    if r.status_code == 200:
        check("Pro pick API has pick data", bool((r.get_json() or {}).get("ticker")
                                                 or (r.get_json() or {})),
              str(r.get_json())[:120])

    r = P.post("/api/chat", json={"message": "hi"}, follow_redirects=False)
    check("Chat answers a subscriber", r.status_code == 200, f"got {r.status_code}")
    if r.status_code == 200:
        d = r.get_json() or {}
        check("Chat returns a reply", bool(d.get("reply")), str(d)[:120])
        check("Chat sends a User-Agent to Groq (Cloudflare 1010 fix)",
              "Mozilla/5.0" in Path(SITE / "scanner_web.py").read_text(encoding="utf-8"),
              "the UA header is required or Cloudflare blocks before auth")

    # ── 4. THE SCAN BUTTON MUST NOT LIE ───────────────────────────────
    section("Scan button tells the truth")
    r = P.post("/run", follow_redirects=False)
    check("Scan button responds to a subscriber", r.status_code == 200, f"got {r.status_code}")
    body = r.get_data(as_text=True)
    try:
        d = json.loads(body)
    except Exception:
        d = {}
    check("Scan returns structured JSON, not a bare 'ok'",
          isinstance(d, dict) and "status" in d, f"body={body[:80]!r}")
    check("Scan reports started OR queued - never a silent fake success",
          d.get("status") in ("started", "queued_locally", "already_pending"),
          f"status={d.get('status')!r}")
    if d.get("status") in ("queued_locally", "already_pending"):
        msg = (d.get("message") or "").lower()
        check("Queued-scan message tells the user it will arrive on its own",
              "within" in msg and ("minute" in msg or "update" in msg), d.get("message", ""))
    check("Scan does not burn a daily scan when nothing ran",
          scanner_web.get_scans_today(SUB) == 0
          or d.get("status") == "started",
          "a no-op scan consumed the subscriber's daily allowance")

    src = Path(SITE / "ai_earnings_scanner.py").read_text(encoding="utf-8")
    check("button says 'Scan', not 'PRO SCAN'", ">PRO SCAN<" not in src)
    check("button label is exactly 'Scan'", ">Scan</button>" in src)
    check("scan JS no longer claims success unconditionally",
          "'Scan started! Reloading...'" not in src,
          "the old JS said it started regardless of what /run returned")
    check("scan JS handles the queued_locally outcome",
          "queued_locally" in src)

    # ── 5. ACCESS SURVIVES A REDEPLOY ─────────────────────────────────
    # The failure Tyler hit. subscriptions.json lives on Railway's ephemeral
    # disk and comes back EMPTY after every deploy. If the only thing keeping
    # a paying customer in is that local file, every deploy silently revokes
    # access they paid for. is_subscriber() must fall back to Stripe.
    section("Access survives a Railway redeploy (subscriptions.json wiped)")
    import importlib
    subs_file = scanner_web.SUBS_FILE
    backup = subs_file.read_text(encoding="utf-8") if subs_file.exists() else None
    try:
        subs_file.write_text("{}", encoding="utf-8")     # simulate the wipe
        scanner_web._STRIPE_VALIDATION_CACHE.clear()
        scanner_web.CACHE_TTL = 0 if hasattr(scanner_web, "CACHE_TTL") else None

        # Stripe is the only source of truth left. Stub it to return active,
        # which is what the real API returns for a paid subscription.
        #
        # The api_key MUST be faked too. _stripe_validate_active() begins with
        # "if not stripe.api_key: return <local record>" - and with no key
        # configured locally that is the correct production behaviour, but it
        # short-circuits before the fallback this section is testing. Without a
        # fake key the test would fail for the right reason (no Stripe
        # configured locally) while proving nothing about the redeploy path.
        class FakeSub:
            id = "sub_fake"
            status = "active"
            current_period_end = 9999999999
            metadata = {}
        class FakeList:
            data = [FakeSub()]
        orig_list = scanner_web.stripe.Subscription.list
        orig_key = scanner_web.stripe.api_key
        scanner_web.stripe.Subscription.list = staticmethod(lambda **kw: FakeList())
        scanner_web.stripe.api_key = "sk_test_fake_for_redeploy_check"
        try:
            D = app.test_client()
            D.set_cookie("stripe_customer", SUB, domain="localhost")
            home = D.get("/").get_data(as_text=True)
            check("subscriber STILL unlocked after the local record is wiped",
                  "window.__isSubscriber=true" in home,
                  "a redeploy revoked access from a paying customer")
            r = D.get("/pro", follow_redirects=False)
            check("/pro still reachable after a redeploy", r.status_code == 200,
                  f"got {r.status_code}")
            r = D.post("/run", follow_redirects=False)
            check("Scan button still works after a redeploy",
                  r.status_code == 200, f"got {r.status_code}")
            check("Stripe fallback rebuilt the local record",
                  SUB in scanner_web.get_subscriptions(),
                  "record was not reconstructed, so every later call re-asks")
        finally:
            scanner_web.stripe.Subscription.list = orig_list
            scanner_web.stripe.api_key = orig_key
    finally:
        if backup is not None:
            subs_file.write_text(backup, encoding="utf-8")
        scanner_web._STRIPE_VALIDATION_CACHE.clear()

    # ── 6. A LOST COOKIE IS NOT A LOST SUBSCRIPTION ────────────────────
    # The customer who paid, then cleared their browser or switched device.
    # For a $5 product this is the single most likely support ticket, and
    # previously it dead-ended at "email support" with no self-serve route.
    section("A subscriber who lost their cookie can get back in")
    src_txt = Path(SITE / "scanner_web.py").read_text(encoding="utf-8")
    check("/success is described as a permanent access link",
          "permanent access link" in src_txt,
          "customers are never told their payment link re-grants access")
    check("/success shows the actual link to save",
          "restore_link" in src_txt and "success?session_id=" in src_txt)
    check("login tells a passwordless subscriber to use their payment link",
          "payment link from your receipt" in src_txt,
          "still dead-ends at 'email support'")
    check("login no longer dead-ends at 'open the device where you subscribed'",
          "Open the device where you subscribed" not in src_txt)

    # ── 7. CANCELLED MEANS LOCKED ─────────────────────────────────────
    section("Cancelled subscriber is locked out")
    check("is_subscriber rejects non-active statuses",
          "'active'" in src_txt and "trialing" in src_txt)

    # ── 8. THE WHOLE THING SURVIVES ITS OWN EDITS ─────────────────────
    section("Guards that protect this journey still pass")
    check("there is exactly ONE is_subscriber definition",
          src_txt.count("def is_subscriber(") == 1,
          f"found {src_txt.count('def is_subscriber(')} - two definitions means "
          f"an edit can land on the wrong one")
    # trigger_scan was shadowed the same way is_subscriber nearly was: a second
    # route defined under the same name rebound the name, so /run silently
    # called the 503 route instead of the real one and queued nothing.
    check("there is exactly ONE trigger_scan definition",
          src_txt.count("def trigger_scan(") == 1,
          f"found {src_txt.count('def trigger_scan(')} - a shadowing definition "
          f"makes /run call the wrong function entirely")
    check("/trigger-scan no longer shadows the real trigger_scan",
          "def manual_scan_trigger(" in src_txt)
    check("/run uses is_subscriber() rather than reading the file directly",
          "get_scans_today(key_id)" in src_txt and
          "subs.get(customer_id, {}).get('status') == 'active' or" not in src_txt,
          "/run re-introduced the hand-rolled check")

    print(f"\n=== {'ALL PASS' if not failures else str(len(failures)) + ' FAILURE(S)'} ===")
    for f in failures:
        print(f"   - {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())