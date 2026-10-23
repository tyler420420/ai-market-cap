#!/usr/bin/env python3
"""Live two-sided paywall audit against the deployed site.

Local guards prove the code is right. They cannot prove Railway is serving it.
This hits https://aismarketcap.com and checks BOTH directions:

  stranger   -> no entry / target / stop number anywhere in the response
  subscriber -> the numbers ARE there, both blur overlays are gone, and
                neither "Unlock PRO Targets" nor "See Entry, Targets" appears

It also gates on /api/visitors returning 200, which is the only signal that
counts as deployed.

Read-only. Writes nothing. No credentials are echoed.
"""
import http.cookiejar
import re
import sys
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
BASE = "https://aismarketcap.com"
SUB = "cus_VTsULOjOP83NeP"          # Tyler's own active record, not a secret
RESTORE = ("/success?session_id=cs_live_b1rZmCCttfl2jgWAesa5sOA8SW2cuGhl8wKzwt"
           "UW2m4qClvemxJWEJwQda")

METRIC = re.compile(
    r">(3D TARGET|7D TARGET|14D TARGET|STOP)</div>\s*<div[^>]*>\$([0-9,]+)")

failures = []


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL") + f"  {name}" + ("" if ok else f"  -- {detail}"))
    if not ok:
        failures.append(name)


def opener(cookie=None):
    jar = http.cookiejar.CookieJar()

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
    return op.open(urllib.request.Request(
        BASE + path, headers={"User-Agent": UA}), timeout=40)


def main():
    # ── deploy gate ──────────────────────────────────────────────────────
    print("=== Deploy gate ===")
    try:
        r = opener().open(urllib.request.Request(
            BASE + "/api/visitors", headers={"User-Agent": UA}), timeout=25)
        check("/api/visitors returns 200 (Railway serving this build)", r.status == 200,
              f"got {r.status}")
    except urllib.error.HTTPError as e:
        check("/api/visitors returns 200 (Railway serving this build)", False,
              f"HTTP {e.code}")
        return 1

    # ── direction 1: someone who never paid ─────────────────────────────
    print("\n=== Visitor who never paid ===")
    anon = opener().open(urllib.request.Request(
        BASE + "/", headers={"User-Agent": UA}), timeout=40)
    html = anon.read().decode("utf-8", "replace")
    print(f"  page length: {len(html)}")
    leaked = METRIC.findall(html)
    check("no entry/target/stop values in the response", not leaked,
          f"LEAKED {leaked}")
    check("the site is serving the NEW build (teaser present)", "pro-teaser" in html,
          "no teaser - this is still the old blur-only build")
    check("paywall markers are not shipped to the browser",
          "PROVALUES" not in html and "PROCTA" not in html)
    check("the pitch is still there", "See Entry, Targets" in html)

    # ── direction 2: Tyler, who paid ────────────────────────────────────
    print("\n=== Subscriber (paid) ===")
    op = opener(SUB)
    op.open(urllib.request.Request(BASE + RESTORE,
                                   headers={"User-Agent": UA}), timeout=40)
    r = op.open(urllib.request.Request(BASE + "/", headers={"User-Agent": UA}),
                timeout=40)
    html2 = r.read().decode("utf-8", "replace")
    vals = METRIC.findall(html2)
    check("subscriber flag set", "window.__isSubscriber=true" in html2)
    check("subscriber DOES receive the paid values", bool(vals),
          "paying and still getting nothing")
    print(f"        subscriber sees: {vals}")
    check("Today's Pick overlay REMOVED", 'id="pro-gate"' not in html2,
          "still blurred for a paying subscriber")
    check("Runner Up overlay REMOVED", 'class="ru-pro-gate"' not in html2,
          "still blurred for a paying subscriber")
    check("no backdrop-blur left over the pick banners",
          "backdrop-filter:blur(4px)" not in html2)
    check("'Unlock PRO Targets' REMOVED", "Unlock PRO Targets" not in html2)
    check("'See Entry, Targets' REMOVED", "See Entry, Targets" not in html2)
    check("targets are not clipped by overflow:hidden",
          "position:relative;overflow:hidden" not in html2)

    print(f"\n=== {'ALL PASS' if not failures else str(len(failures)) + ' FAILURE(S)'} ===")
    for f in failures:
        print(f"   - {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())