#!/usr/bin/env python3
"""Prove the Pro paywall actually holds, and that subscribers really unlock.

WHY THIS EXISTS
---------------
Tyler 2026-10-22, screenshot of both pick banners blurred with "Unlock PRO
Targets" and "See Entry, Targets & Stops" still showing, in subscriber mode:
"the pro subscriber should have todays pick and runner up picks unlocked and not
blurred with the buttons removed since they paid."

Before fixing the styling, the PUBLIC response was audited. It contained:

    3D TARGET   $145
    STOP        $84
    3D TARGET   $1248
    STOP        $803

in plain text. The blur was a CSS overlay over data already downloaded, so
view-source read the entire $5 product for free. The paywall was decorative.

This tests BOTH directions against the real Flask app, and specifically checks
the leak rather than the appearance:

  non-subscriber -> the paid numbers are ABSENT from the response body
  subscriber     -> the numbers are present, the overlays are GONE, and the
                    "unlock" buttons are GONE too (they paid; stop asking)

The appearance of a blur is not the property that matters. Absence of the data
is.

Run:  python verify_paywall.py
Exit 0 = all pass.
"""
import re
import sys
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
sys.path.insert(0, str(SITE))

failures = []
SUB = "cus_VTsULOjOP83NeP"

# Label -> value, as rendered in each metric box.
# The banners moved from TARGET/3D TARGET/5D TARGET to a LONG and SHORT row
# each carrying ENTRY / 3D TGT / 7D TGT / 14D TGT / STOP. This is the leak
# detector, so it must match EVERY caption that can hold a paid number -
# a caption added to the banner and not added here reads as "no leak" while
# shipping the whole product.
METRIC = re.compile(
    r">(ENTRY|3D TGT|7D TGT|14D TGT|STOP|TARGET|3D TARGET|5D TARGET)</div>\s*"
    r"<div[^>]*>\$([0-9,]+)")


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL") + f"  {name}" + ("" if ok else f"  -- {detail}"))
    if not ok:
        failures.append(name)


def main():
    import scanner_web as S

    app = S.app
    app.config["TESTING"] = True

    # ── 1. NON-SUBSCRIBER: no paid values on the wire --------------------
    print("=== Non-subscriber (never paid) ===")
    anon = app.test_client()
    html = anon.get("/").get_data(as_text=True)
    leaked = METRIC.findall(html)
    check("NO entry/target/stop values in a non-subscriber's HTML",
          not leaked,
          f"LEAKED {leaked}" if leaked else "")
    check("no bare dollar values in the PRO metrics strip",
          "PRO:</span>" not in html or not re.search(
              r"PRO:</span>.{0,400}?\$\d", html, re.S),
          "a $ figure is sitting next to the PRO label")
    check("teaser is shown instead of the numbers", "pro-teaser" in html)
    check("subscribe CTA is still present (that is the pitch)",
          "See Entry, Targets" in html)
    check("blur overlay is present for non-subscribers", "pro-gate" in html)

    # ── 2. SUBSCRIBER: unlocked, and the buttons are gone -----------------
    print("\n=== Active subscriber ===")
    P = app.test_client()
    P.set_cookie("stripe_customer", SUB, domain="localhost")
    html = P.get("/").get_data(as_text=True)

    check("subscriber flag is set", "window.__isSubscriber=true" in html)

    vals = METRIC.findall(html)
    check("subscriber DOES receive the paid values", bool(vals),
          "subscriber is paying and still gets nothing")
    print(f"        subscriber sees: {vals[:6]}")

    check("Today's Pick overlay is REMOVED",
          'id="pro-gate"' not in html,
          "still blurred for a paying subscriber")
    check("Runner Up overlay is REMOVED",
          'class="ru-pro-gate"' not in html,
          "still blurred for a paying subscriber")
    check("no backdrop-blur remains over the pick banners",
          "backdrop-filter:blur(4px)" not in html,
          "a blur overlay is still shipped to a subscriber")
    check("'See Entry, Targets' upsell button is REMOVED for a subscriber",
          "See Entry, Targets" not in html,
          "they are being asked to unlock what they already bought")
    check("'Unlock PRO Targets' button is REMOVED for a subscriber",
          "Unlock PRO Targets" not in html,
          "they are being asked to unlock what they already bought")
    check("overflow:hidden no longer clips the subscriber's targets",
          "position:relative;overflow:hidden" not in html,
          "targets are rendered but clipped by CSS")
    check("Pro badge shown instead of Subscribe",
          "pro-account-badge" in html)

    # ── 3. the ask-ai entry point is usable by a subscriber --------------
    print("\n=== Ask AI for a subscriber ===")
    r = P.post("/api/chat", json={"message": "what is todays pick"},
               follow_redirects=False)
    check("chat answers a subscriber", r.status_code == 200, f"got {r.status_code}")
    if r.status_code == 200:
        reply = (r.get_json() or {}).get("reply", "")
        check("chat returns a real grounded answer",
              len(reply) > 30 and "trouble connecting" not in reply.lower()
              and "warming up" not in reply.lower(), reply[:90])

    # ── 4. the leak cannot come back through the raw file ----------------
    print("\n=== The served file itself ===")
    raw = (SITE / "ai_earnings_today.html").read_text(encoding="utf-8")
    check("the static file carries the paywall markers",
          "<!--PROVALUES-->" in raw and "<!--/PROVALUES-->" in raw,
          "markers missing, so the server cannot strip anything")
    check("markers appear once per banner (2 banners)", raw.count("<!--PROVALUES-->") == 2,
          f"found {raw.count('<!--PROVALUES-->')}")
    check("every PROVALUES opener is PAIRED with a closer",
          raw.count("<!--PROVALUES-->") == raw.count("<!--/PROVALUES-->"),
          f"{raw.count('<!--PROVALUES-->')} open vs "
          f"{raw.count('<!--/PROVALUES-->')} close - an unpaired opener "
          f"strips nothing and leaks the whole product")
    check("every PROCTA opener is PAIRED with a closer",
          raw.count("<!--PROCTA-->") == raw.count("<!--/PROCTA-->"),
          f"{raw.count('<!--PROCTA-->')} open vs "
          f"{raw.count('<!--/PROCTA-->')} close")
    check("both CTA blocks per banner are marked (top-row link + overlay)",
          raw.count("<!--PROCTA-->") == 4,
          f"found {raw.count('<!--PROCTA-->')}, expected 4")
    check("markers never reach the browser (stripped at serve time)",
          "PROVALUES" not in html and "PROCTA" not in html,
          "raw marker text leaked into the response")

    # ── 5. the marked block actually CONTAINS the values ------------------
    # A correctly paired marker placed in the wrong spot strips an empty
    # region and ships every number. Assert the values are INSIDE it.
    print("\n=== Marker placement (the bug that leaked $145) ===")
    blocks = re.findall(r'<!--PROVALUES-->(.*?)<!--/PROVALUES-->', raw, re.S)
    check("two PROVALUES blocks found in the file", len(blocks) == 2, f"got {len(blocks)}")
    for n, b in enumerate(blocks, 1):
        vals = METRIC.findall(b)
        check(f"block {n} contains the paid metric boxes", bool(vals), f"block is empty: {b[:80]!r}")
        print(f"        block {n} holds: {vals}")

    # ── 6. fails CLOSED, not open ----------------------------------------
    # The single most dangerous failure here is silent: helper finds an
    # opening marker, no closer, returns the page untouched, and the paid
    # numbers go out to the public with a guard reporting green.
    print("\n=== Fail-closed behaviour ===")
    # Opener FIRST, values after it, no closer - the realistic broken shape.
    broken = ('<div class="pro-values-box">'
              + S.VALUES_OPEN
              + '<div>3D TARGET</div><div>$145</div>'
                '<div>STOP</div><div>$84</div>'
              + S.CTA_OPEN + '<a href="/pricing">See Entry</a></div>'
                '<footer>the rest of the page</footer>')
    out = S._strip_pro_values(broken)
    check("unpaired PROVALUES still removes the values (no silent pass-through)",
          "$145" not in out and "$84" not in out, f"LEAKED: {out[-90:]}")
    check("unpaired PROVALUES degrades to the teaser, not a blank box",
          "pro-teaser" in out)
    check("unpaired PROVALUES leaves the CTA block intact for the pitch",
          "See Entry" in out)
    check("unpaired PROVALUES does NOT truncate the page",
          "the rest of the page" in out,
          "fail-closed path destroyed the document tail")

    broken_cta = ('<p>intro</p>' + S.CTA_OPEN
                  + '<a href="/pricing">See Entry</a><footer>tail</footer>')
    out2 = S._strip_block(broken_cta, S.CTA_OPEN)
    check("unpaired PROCTA is removed rather than left on the page",
          "See Entry" not in out2, f"CTA survived: {out2[-90:]}")
    check("unpaired PROCTA removes only the button, keeps the rest of the page",
          "the rest" not in out2 and "tail" in out2 and "intro" in out2,
          f"got: {out2[-90:]}")
    check("both fail-closed helpers keep their surrounding document",
          "pro-values-box" in out and "intro" in out2 and "tail" in out2)

    # positive control: a correctly paired block IS stripped
    paired = ('<!--PROVALUES--><div>3D TARGET</div><div>$145</div>'
              '<!--/PROVALUES--><p>after</p>')
    out3 = S._strip_pro_values(paired)
    check("positive control: paired block is stripped",
          "$145" not in out3 and "after" in out3)

    # ── 7. real artifact, both branches, both directions -----------------
    print("\n=== Real artifact through both branches ===")
    non_sub = S._strip_pro_values(raw)
    check("real artifact: no values for a stranger", not METRIC.findall(non_sub),
          f"LEAKED {METRIC.findall(non_sub)}")
    sub_html = S._strip_block(raw, S.CTA_OPEN)
    sub_html = S._strip_element(S._strip_element(sub_html, 'pro-gate'), 'ru-pro-gate')
    check("real artifact: values survive for a subscriber", bool(METRIC.findall(sub_html)))
    check("real artifact: no upsell text for a subscriber",
          "See Entry, Targets" not in sub_html and "Unlock PRO Targets" not in sub_html)

    print(f"\n=== {'ALL PASS' if not failures else str(len(failures)) + ' FAILURE(S)'} ===")
    for f in failures:
        print(f"   - {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())