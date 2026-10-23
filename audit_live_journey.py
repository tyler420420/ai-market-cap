"""End-to-end subscriber journey against the LIVE site, plus product checks
for the growth question.

Every route a paying customer can reach, driven as a real subscriber session
with the real restore link. Read-only: no checkout session is created, so
nothing is written to Stripe.
"""
import http.cookiejar
import re
import sys
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
BASE = "https://aismarketcap.com"
SUB = "cus_VTsULOjOP83NeP"
RESTORE = ("/success?session_id=cs_live_b1rZmCCttfl2jgWAesa5sOA8SW2cuGhl8wKzwt"
           "UW2m4qClvemxJWEJwQda")

failures = []
LAST_JAR = []


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL") + f"  {name}" + ("" if ok else f"  -- {detail}"))
    if not ok:
        failures.append(name)


def opener(cookie=None):
    jar = http.cookiejar.CookieJar()
    LAST_JAR.append(jar)

    class NoRedir(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    op = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar), NoRedir)
    if cookie:
        jar.set_cookie(http.cookiejar.Cookie(
            version=0, name="stripe_customer", value=cookie, port=None,
            port_specified=False, domain="aismarketcap.com",
            domain_specified=True, domain_initial_dot=False, path="/",
            path_specified=True, secure=False, expires=None, discard=False,
            comment=None, comment_url=None, rest={}, rfc2109=False))
    return op


def get(op, path):
    return op.open(urllib.request.Request(BASE + path,
                                          headers={"User-Agent": UA}),
                   timeout=40)


def main():
    try:
        r = opener().open(urllib.request.Request(
            BASE + "/api/visitors", headers={"User-Agent": UA}), timeout=25)
        check("deploy gate /api/visitors 200", r.status == 200, f"got {r.status}")
    except urllib.error.HTTPError as e:
        check("deploy gate /api/visitors 200", False, f"HTTP {e.code}")
        return 1

    # Ã¢â€â‚¬Ã¢â€â‚¬ 1. the restore link every customer is emailed Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
    print("\n=== 1. Subscriber restores access from the emailed link ===")
    op = opener(SUB)
    r = op.open(urllib.request.Request(BASE + RESTORE,
                                       headers={"User-Agent": UA}), timeout=40)
    body = r.read().decode("utf-8", "replace")
    check("restore link returns 200", r.status == 200)
    check("restore link confirms payment", "Payment Successful" in body)
    check("restore link is presented as a permanent access link",
          "permanent access link" in body,
          "a customer who clears cookies has no route back")
    check("a cookie was actually set",
          any(c.name == "stripe_customer" for c in LAST_JAR[-1]))

    # Ã¢â€â‚¬Ã¢â€â‚¬ 2. every page a subscriber can reach Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
    print("\n=== 2. Every subscriber route ===")
    for path, needle, label in (("/", "__isSubscriber=true", "scanner"),
                                ("/pro", "Pro Dashboard", "Pro dashboard"),
                                ("/account", None, "account page"),
                                ("/pricing", "$5", "pricing")):
        try:
            rr = op.open(urllib.request.Request(
                BASE + path, headers={"User-Agent": UA}), timeout=40)
            b = rr.read().decode("utf-8", "replace")
            check(f"{label} reachable", rr.status == 200, f"HTTP {rr.status}")
            if needle:
                check(f"{label} shows subscriber state", needle in b)
        except urllib.error.HTTPError as e:
            check(f"{label} reachable", False, f"HTTP {e.code}")

    try:
        rr = op.open(urllib.request.Request(
            BASE + "/api/pro_pick", headers={"User-Agent": UA}), timeout=40)
        pb = rr.read().decode("utf-8", "replace")
        check("pro pick API returns the paid data",
              rr.status == 200 and ("ticker" in pb or "target" in pb),
              pb[:90])
    except urllib.error.HTTPError as e:
        check("pro pick API returns the paid data", False, f"HTTP {e.code}")

    # Ã¢â€â‚¬Ã¢â€â‚¬ 3. the two things they actually pay to use Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
    print("\n=== 3. Ask AI + sort ===")
    req = urllib.request.Request(
        BASE + "/api/chat",
        data=b'{"message":"what is my target and stop"}',
        headers={"User-Agent": UA, "Content-Type": "application/json"},
        method="POST")
    try:
        rr = op.open(req, timeout=45)
        import json
        reply = (json.loads(rr.read().decode("utf-8", "replace")) or {}).get("reply", "")
        check("Ask AI answers a real question",
              rr.status == 200 and len(reply) > 20 and "$" in reply, reply[:70])
    except urllib.error.HTTPError as e:
        check("Ask AI answers a real question", False, f"HTTP {e.code}")

    home = op.open(urllib.request.Request(BASE + "/",
                                          headers={"User-Agent": UA}),
                   timeout=40).read().decode("utf-8", "replace")
    check("table headers call the sort handler", "onHeaderClick(" in home)
    check("no header redirects to /pricing any more",
          "location.href='https://aismarketcap.com/pricing'" not in home)
    check("banner is not blurred for them", "backdrop-filter:blur(4px)" not in home)
    check("no upsell buttons shown to them",
          "Unlock PRO Targets" not in home and "See Entry, Targets" not in home)

    # Ã¢â€â‚¬Ã¢â€â‚¬ 4. product surface, for the growth question Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
    # These three originally passed for the WRONG reason and are worth the
    # extra care: a guard that matches nothing reports ALL PASS.
    #   - the author regex looked for "&mdash;" but the page emits a literal
    #     U+2014, so it matched zero and "no fake testimonials" passed vacuously
    #   - "subscribe" matched the nav button text, not an email form
    #   - "+%" does not match "+57.3%", so the wins page looked empty
    print("\n=== 4. Growth surface: what exists today ===")
    anon = opener().open(urllib.request.Request(
        BASE + "/", headers={"User-Agent": UA}), timeout=40).read().decode("utf-8", "replace")
    pricing = opener().open(urllib.request.Request(
        BASE + "/pricing", headers={"User-Agent": UA}), timeout=40).read().decode("utf-8", "replace")

    authors = re.findall(r'class=author[^>]*>(.*?)</div>', pricing, re.S)
    print(f"        named endorsements on the checkout page: {len(authors)}")
    for a in authors:
        print(f"          {a.strip()[:60]}")
    check("checkout page carries NO named endorsements",
          not authors,
          f"{len(authors)} named testimonials sit next to the pay button - "
          f"this is an FTC endorsement exposure and a trust risk")

    has_email_input = bool(re.search(r'type=["\']email["\']', anon, re.I))
    check("there IS a real email-capture form on the free page",
          has_email_input,
          "the only <input> is the chat box - a free visitor who is not ready "
          "to pay is unreachable, and there is no owned channel at all")

    alerts_promised = "earnings alerts" in pricing.lower()
    print(f"        'earnings alerts' promised on pricing: {alerts_promised}")
    check("every paid feature listed on pricing is actually delivered",
          not alerts_promised,
          "pricing sells 'real-time earnings alerts' and the repo has no "
          "outbound email or push transport at all")

    try:
        wins = opener().open(urllib.request.Request(
            BASE + "/wins", headers={"User-Agent": UA}), timeout=40).read().decode("utf-8", "replace")
        gains = re.findall(r'\+\d+(?:\.\d+)?%', wins)
        print(f"        wins page: {len(gains)} real gains, {len(wins)} bytes")
        check("wins page shows real numbers (the honest alternative to fake quotes)",
              len(gains) >= 5,
              f"only {len(gains)} gains found - the +N% regex must allow decimals")
    except urllib.error.HTTPError as e:
        check("wins page reachable", False, f"HTTP {e.code}")

    print(f"\n=== {'ALL PASS' if not failures else str(len(failures)) + ' ISSUE(S) FOUND'} ===")
    for f in failures:
        print(f"   - {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

