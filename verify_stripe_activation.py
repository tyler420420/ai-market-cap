"""Regression test: a real Stripe payment must actually activate the account.

THE BUG
-------
stripe-python >= 7 returns StripeObject (Session/Subscription/Customer), which
is NOT a dict subclass. The webhook and /success handlers called .get() on
those objects, which raised AttributeError, so save_subscription() was never
reached. The buyer's card was charged and they were shown "Payment received
but there was a problem activating your account".

This test builds REAL StripeObject instances (not dicts), drives the real
Flask routes with a valid signature, and asserts the subscription is actually
written. A dict-shaped fake would pass even with the bug, which is exactly why
this test uses construct_from().

Run:  python verify_stripe_activation.py
Exit 0 = all checks passed.
"""

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).parent / "scanner_web.py"

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  -- {detail}" if detail and not cond else ""))


with tempfile.TemporaryDirectory() as td:
    tmp_src = Path(td) / "scanner_web.py"
    tmp_src.write_text(SRC.read_text(encoding="utf-8"), encoding="utf-8")
    subs_path = Path(td) / "subscriptions.json"

    spec = importlib.util.spec_from_file_location("sw_stripe_test", tmp_src)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["sw_stripe_test"] = mod
    spec.loader.exec_module(mod)

    import stripe

    # Point the store at the temp dir and give us a real signing secret.
    mod.SUBS_FILE = subs_path
    mod.STRIPE_WEBHOOK_SECRET = "whsec_test_secret_for_local_verification"
    mod.app.config["TESTING"] = True
    client = mod.app.test_client()

    def sign(payload):
        """Stripe signature header for a payload, as the ROUTE will see it.

        The route passes request.data (bytes) to construct_event, and
        verify_header() does not decode bytes - it signs "%d.%s" against the raw
        argument. So a signature computed over the str form is REJECTED against
        the bytes form. Both sides must be signed over the SAME type the route
        receives, which is why this deliberately takes the bytes.
        """
        import hmac
        import hashlib
        import time as _time
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        ts = int(_time.time())
        # Mirror Stripe: signed payload is b"<ts>." + payload
        signed = str(ts).encode("utf-8") + b"." + payload
        mac = hmac.new(mod.STRIPE_WEBHOOK_SECRET.encode("utf-8"),
                       signed, hashlib.sha256).hexdigest()
        return f"t={ts},v1={mac}"

    def event(etype, obj, evt_id="evt_1"):
        """A webhook body shaped like a real Stripe event.

        The top-level "object":"event" field is REQUIRED: stripe-python 15 reads
        event.object to detect thin (v2) notifications, and a payload without it
        raises AttributeError before any of our code runs. Real Stripe always
        sends it; omitting it here produced a test failure that looked like a
        webhook bug when it was really a fixture bug.
        """
        return json.dumps({
            "id": evt_id, "object": "event", "api_version": "2024-06-20",
            "created": 1700000000, "type": etype,
            "data": {"object": obj},
        }).encode("utf-8")

    def read_subs():
        if not subs_path.exists():
            return {}
        return json.loads(subs_path.read_text(encoding="utf-8"))

    # ---- REAL StripeObject, not a dict -----------------------------------
    print("=== 1. _plain() converts a real StripeObject ===")
    real = stripe.Event.construct_from({
        "id": "evt_1", "type": "checkout.session.completed",
        "data": {"object": {
            "id": "cs_test_1", "object": "checkout.session",
            "customer": "cus_test_1", "customer_email": "tyler@example.com",
            "subscription": "sub_test_1", "metadata": {"plan": "monthly"},
            "customer_details": {"email": "tyler@example.com", "name": "Tyler"},
        }}}, "sk_test_x")
    raw_obj = real["data"]["object"]
    check("payload really is a StripeObject", not isinstance(raw_obj, dict),
          f"type={type(raw_obj).__name__}")
    try:
        raw_obj.get("customer")
        raised = False
    except AttributeError:
        raised = True
    check("raw StripeObject has no .get() (the original bug)", raised,
          "if this passes the bug may not reproduce with this stripe version")
    plain = mod._plain(raw_obj)
    check("_plain() gives a real dict", isinstance(plain, dict), type(plain).__name__)
    check("_plain() keeps the values", plain.get("customer") == "cus_test_1", repr(plain)[:120])
    check("_plain() recurses into metadata",
          isinstance(plain.get("metadata"), dict) and plain["metadata"].get("plan") == "monthly",
          repr(plain.get("metadata")))
    check("_plain(None) is safe", mod._plain(None) == {})

    # ---- WEBHOOK: the money path ------------------------------------------
    print("\n=== 2. checkout.session.completed activates the account ===")
    body = event("checkout.session.completed", {
        "id": "cs_test_2", "object": "checkout.session",
        "customer": "cus_test_2", "customer_email": "buyer@example.com",
        "subscription": "sub_test_2", "metadata": {"plan": "annual"},
        "customer_details": {"email": "buyer@example.com"},
    }, "evt_2")

    # No Stripe API key -> retrieve() calls are skipped, isolating the handler.
    mod.stripe.api_key = ""
    r = client.post("/webhook", data=body.decode("utf-8"),
                    headers={"Stripe-Signature": sign(body)})
    check("webhook returned 200", r.status_code == 200, f"{r.status_code} {r.data[:200]}")
    s = read_subs()
    check("subscription WAS saved (was NOT before the fix)",
          "cus_test_2" in s, f"subscriptions={list(s)}")
    if "cus_test_2" in s:
        rec = s["cus_test_2"]
        check("status is active", rec.get("status") == "active", repr(rec.get("status")))
        check("plan captured from metadata", rec.get("plan") == "annual", repr(rec.get("plan")))
        check("email captured", rec.get("email") == "buyer@example.com", repr(rec.get("email")))
        check("sub_id captured", rec.get("sub_id") == "sub_test_2", repr(rec.get("sub_id")))

    print("\n=== 3. the other event types activate too ===")
    for etype, obj, expect_cust in [
        ("customer.subscription.created",
         {"id": "sub_3", "object": "subscription", "customer": "cus_test_3",
          "status": "active", "metadata": {"plan": "monthly"},
          "current_period_end": 1800000000}, "cus_test_3"),
        ("customer.subscription.updated",
         {"id": "sub_4", "object": "subscription", "customer": "cus_test_4",
          "status": "active", "metadata": {"plan": "monthly"},
          "current_period_end": 1800000000}, "cus_test_4"),
        ("customer.subscription.deleted",
         {"id": "sub_5", "object": "subscription", "customer": "cus_test_5",
          "status": "canceled", "metadata": {"plan": "monthly"}}, "cus_test_5"),
        ("checkout.session.async_payment_succeeded",
         {"id": "cs_6", "object": "checkout.session", "customer": "cus_test_6",
          "customer_email": "ach@example.com", "metadata": {"plan": "monthly"},
          "customer_details": {"email": "ach@example.com"}}, "cus_test_6"),
    ]:
        b = event(etype, obj, f"evt_{etype}")
        rr = client.post("/webhook", data=b.decode("utf-8"),
                         headers={"Stripe-Signature": sign(b)})
        ss = read_subs()
        check(f"{etype} saved a subscription",
              rr.status_code == 200 and expect_cust in ss,
              f"http={rr.status_code} saved={list(ss)}")
    d5 = read_subs().get("cus_test_5", {})
    check("deletion marks cancelled, not active",
          d5.get("status") == "cancelled", repr(d5.get("status")))

    print("\n=== 4. renewal keeps access, failed payment marks past_due ===")
    for etype, cust, want in [("invoice.payment_succeeded", "cus_test_4", "active"),
                              ("invoice.payment_failed", "cus_test_4", "past_due")]:
        b = event(etype, {"id": "in_1", "object": "invoice", "customer": cust,
                        "period_end": 1800000000}, f"evt_{etype}")
        client.post("/webhook", data=b.decode("utf-8"),
                    headers={"Stripe-Signature": sign(b)})
        got = read_subs().get(cust, {}).get("status")
        check(f"{etype} -> {want}", got == want, f"got {got}")

    print("\n=== 5. unknown/duplicate events are harmless ===")
    b = event("some.other.event", {"id": "x", "foo": "bar"}, "evt_9")
    r9 = client.post("/webhook", data=b.decode("utf-8"),
                     headers={"Stripe-Signature": sign(b)})
    check("unknown event still 200", r9.status_code == 200, str(r9.status_code))

    print("\n=== 6. signature is still enforced (fix did not weaken auth) ===")
    b = event("checkout.session.completed",
            {"id": "cs", "object": "checkout.session", "customer": "cus_bad"}, "evt_bad")
    rb = client.post("/webhook", data=b, headers={"Stripe-Signature": "t=1,v1=deadbeef"})
    check("forged signature rejected", rb.status_code == 400, str(rb.status_code))
    check("forged signature saved nothing", "cus_bad" not in read_subs())

    print("\n=== 7. /success activates the account (Tyler's exact screen) ===")
    # This is the page the buyer lands on after paying, and the one that
    # produced "Payment received but there was a problem activating your
    # account". It fetches the checkout Session and calls .get() on it - the
    # same StripeObject mistake as the webhook, on an independent code path.
    real_session = stripe.checkout.Session.construct_from({
        "id": "cs_success_1", "object": "checkout.session",
        "customer": "cus_success_1", "customer_email": "paid@example.com",
        "subscription": "sub_success_1",
        "metadata": {"plan": "monthly"},
        "customer_details": {"email": "paid@example.com", "name": "Tyler"},
    }, "sk_test_x")
    check("/success fixture is a real StripeObject",
          not isinstance(real_session, dict) and not hasattr(real_session, "get"),
          type(real_session).__name__)

    def fake_retrieve(sid, **kw):
        return real_session

    orig_retrieve = mod.stripe.checkout.Session.retrieve
    mod.stripe.checkout.Session.retrieve = staticmethod(fake_retrieve)
    try:
        rs = client.get("/success?session_id=cs_success_1")
        body_txt = rs.get_data(as_text=True)
        check("/success did not show the activation error",
              "problem activating" not in body_txt.lower(),
              "buyer still sees the failure screen")
        check("/success returned 200", rs.status_code == 200, str(rs.status_code))
        s2 = read_subs()
        check("/success saved the subscription",
              "cus_success_1" in s2, f"saved={list(s2)}")
        if "cus_success_1" in s2:
            rec = s2["cus_success_1"]
            check("/success marked it active", rec.get("status") == "active",
                  repr(rec.get("status")))
            check("/success captured the buyer email",
                  rec.get("email") == "paid@example.com", repr(rec.get("email")))
        check("/success set the customer cookie",
              "stripe_customer=cus_success_1" in rs.headers.get("Set-Cookie", ""),
              rs.headers.get("Set-Cookie", "<none>"))
    finally:
        mod.stripe.checkout.Session.retrieve = orig_retrieve

    print("\n=== 8. account page reads period_end without crashing ===")
    # /account lists subscriptions and calls Subscription.list(); with no key
    # that branch is skipped. Confirms the route still serves.
    ra = client.get("/account", environ_overrides={"HTTP_COOKIE": "stripe_customer=cus_test_2"})
    check("/account does not 500", ra.status_code < 500, str(ra.status_code))

print("\n" + "=" * 62)
failed = [r for r in results if not r[1]]
print(f"{len(results) - len(failed)}/{len(results)} checks passed")
if failed:
    for n, _, d in failed:
        print(f"  FAILED: {n}  {d}")
    sys.exit(1)
print("PAYMENTS ACTIVATE CORRECTLY")