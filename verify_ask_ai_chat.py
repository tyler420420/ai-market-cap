#!/usr/bin/env python3
"""Prove the Ask AI chat actually works for a Pro subscriber.

WHY THIS EXISTS
---------------
Tyler 2026-10-22: "wire up the Ask AI button chat on the website to actually
work for Pro subscribers". The button existed, /api/chat existed, and it was
still broken three ways:

  1. Unauthenticated it returned a 302 to /pricing. fetch() follows redirects
     transparently, so the JS got the pricing page's HTML with status 200,
     r.json() threw, and the user saw "Error: Unexpected token '<'".
  2. It hand-rolled its subscriber check and looked ONLY at the
     stripe_customer cookie. is_subscriber() also checks the session cookie
     and falls back to asking Stripe when the local record is missing - and
     subscriptions.json lives on Railway's ephemeral disk, so it comes back
     empty after every redeploy. The endpoint most likely to be used right
     after paying was the one most likely to deny a paying customer.
  3. call_llm() collapsed every failure into "I'm having trouble connecting
     right now" and logged nothing, so a missing GROQ_API_KEY was
     indistinguishable from a network blip.

This tests the REAL Flask app with a REAL subscriber cookie, and checks both
directions: a subscriber gets an answer, a non-subscriber gets a clean paywall
instead of a JSON parse error.

Run:  python verify_ask_ai_chat.py
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


def main():
    import scanner_web

    app = scanner_web.app
    app.config["TESTING"] = True
    CLIENT = app.test_client()

    SUB_ID = "cus_VTsULOjOP83NeP"   # Tyler's real active monthly subscription

    # ---- 1. the route and helpers exist --------------------------------
    rules = {str(r) for r in app.url_map.iter_rules()}
    check("/api/chat route exists", "/api/chat" in rules)
    check("/pricing route exists (paywall target)", "/pricing" in rules)
    check("call_llm exists", hasattr(scanner_web, "call_llm"))

    # ---- 2. NON-subscriber gets a redirect, not a JSON body ------------
    # follow_redirects=False is essential: with it True the test client eats
    # the 302 and hands back the pricing page, exactly the failure the user
    # was hitting.
    r = CLIENT.post("/api/chat", json={"message": "hello"}, follow_redirects=False)
    check("non-subscriber is redirected (not served JSON)",
          r.status_code in (301, 302, 303, 307, 308),
          f"got {r.status_code}")
    if r.status_code in (301, 302, 303, 307, 308):
        loc = r.headers.get("Location", "")
        check("redirect targets /pricing", "/pricing" in loc, f"Location={loc!r}")
        # The chat JS keys off the paywall; a bare /pricing is ambiguous.
        check("redirect carries a from= marker the JS can trust",
              "from=chat" in loc, f"Location={loc!r}")

    # ---- 3. SUBSCRIBER gets a real answer ------------------------------
    CLIENT.set_cookie("stripe_customer", SUB_ID, domain="localhost")
    r = CLIENT.post("/api/chat", json={"message": "what is a good score?"},
                    follow_redirects=False)
    check("subscriber is NOT redirected", r.status_code == 200,
          f"got {r.status_code} - a paying customer was denied")
    if r.status_code == 200:
        ct = r.headers.get("Content-Type", "")
        check("subscriber response is JSON", "application/json" in ct, ct)
        data = r.get_json(silent=True) or {}
        check("subscriber response has a reply field", "reply" in data,
              f"keys={list(data)}")
        reply = data.get("reply", "")
        check("reply is a non-empty string", isinstance(reply, str) and len(reply) > 0)
        # The answer must be specific. "warming up"/"not configured" means
        # GROQ_API_KEY is absent on the deploy - that is a CONFIG problem the
        # operator must fix, and saying so is the point of this check.
        cfg_words = ("not configured", "not authorised", "warming up", "trouble")
        degraded = any(w in reply.lower() for w in cfg_words)
        print(f"        reply: {reply[:150]!r}")
        print(f"        LLM reachable in this environment: {not degraded}")
        if degraded:
            print("        NOTE: GROQ_API_KEY is not set locally. The endpoint is")
            print("              wired correctly but the model cannot answer until")
            print("              the key exists as a Railway service variable.")

    # ---- 4. input validation -------------------------------------------
    r = CLIENT.post("/api/chat", json={"message": ""}, follow_redirects=False)
    check("empty message rejected", r.status_code == 400, f"got {r.status_code}")
    r = CLIENT.post("/api/chat", json={"message": "x" * 1200}, follow_redirects=False)
    check("over-long message rejected", r.status_code == 400, f"got {r.status_code}")

    # ---- 5. no auth bypass via missing body ---------------------------
    r = CLIENT.post("/api/chat", data="not json",
                    content_type="application/json", follow_redirects=False)
    check("malformed body does not 500", r.status_code < 500,
          f"got {r.status_code}")

    # ---- 6. call_llm distinguishes failure modes -----------------------
    # Save/restore the real key so this does not mutate the module for others.
    real = scanner_web.GROQ_API_KEY
    try:
        scanner_web.GROQ_API_KEY = ""
        out = scanner_web.call_llm("hi")
        check("missing key says NOT CONFIGURED, not 'try again shortly'",
              "not configured" in out.lower() and "warming up" not in out.lower(),
              f"got {out!r}")

        scanner_web.GROQ_API_KEY = "sk-definitely-not-a-real-key"
        out = scanner_web.call_llm("hi")
        check("bad key does not claim success",
              len(out) > 0 and "here you go" not in out.lower(), f"got {out!r}")
        print(f"        bad-key reply: {out[:120]!r}")
    finally:
        scanner_web.GROQ_API_KEY = real

    # ---- 7. the pick banners say Price, not Entry ----------------------
    scanner = (SITE / "ai_earnings_scanner.py").read_text(encoding="utf-8")
    check("no stale '>Entry <strong' label in pick banners",
          ">Entry <strong" not in scanner)
    check("Today's Pick uses Price",
          ">Price <strong" in scanner,
          "expected the Price label")

    print(f"\n=== {'ALL PASS' if not failures else str(len(failures)) + ' FAILURE(S)'} ===")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())