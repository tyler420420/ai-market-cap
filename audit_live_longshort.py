"""Is the deployed site showing the LONG and SHORT plan, and does the paywall
still hold with twice as many numbers on the page?

Doubling the paid values doubles what a leak would expose, so this checks both
directions against the LIVE site rather than the local file.

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
SUB = "cus_VTsULOjOP83NeP"
RESTORE = ("/success?session_id=cs_live_b1rZmCCttfl2jgWAesa5sOA8SW2cuGhl8wKzwt"
           "UW2m4qClvemxJWEJwQda")

METRIC = re.compile(
    r">(ENTRY|3D TGT|7D TGT|14D TGT|STOP|TARGET|3D TARGET|5D TARGET)</div>\s*"
    r"<div[^>]*>\$([0-9,]+)")

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


def main():
    try:
        r = opener().open(urllib.request.Request(
            BASE + "/api/visitors", headers={"User-Agent": UA}), timeout=25)
        check("/api/visitors 200 (deploy gate)", r.status == 200, f"got {r.status}")
    except urllib.error.HTTPError as e:
        check("/api/visitors 200 (deploy gate)", False, f"HTTP {e.code}")
        return 1

    # ── stranger ─────────────────────────────────────────────────────────
    print("\n=== Visitor who never paid ===")
    anon = opener().open(urllib.request.Request(
        BASE + "/", headers={"User-Agent": UA}), timeout=40)
    html = anon.read().decode("utf-8", "replace")
    leaked = METRIC.findall(html)
    check("no ENTRY / 3D / 7D / 14D / STOP values leak", not leaked, f"LEAKED {leaked}")
    check("no LONG or SHORT row leaks", ">LONG</span>" not in html and ">SHORT</span>" not in html)
    check("teaser shown instead", "pro-teaser" in html)

    # ── subscriber ───────────────────────────────────────────────────────
    print("\n=== Subscriber ===")
    op = opener(SUB)
    op.open(urllib.request.Request(BASE + RESTORE,
                                   headers={"User-Agent": UA}), timeout=40)
    r = op.open(urllib.request.Request(BASE + "/", headers={"User-Agent": UA}),
                timeout=40)
    sub = r.read().decode("utf-8", "replace")
    vals = METRIC.findall(sub)
    check("subscriber receives the full plan", len(vals) >= 20,
          f"only {len(vals)} values - expected 2 banners x 2 rows x 5 boxes")
    for label in ("ENTRY", "3D TGT", "7D TGT", "14D TGT", "STOP"):
        check(f"  {label} present", label in sub)
    check("LONG row present", ">LONG</span>" in sub)
    check("SHORT row present", ">SHORT</span>" in sub)
    check("both overlays removed",
          'id="pro-gate"' not in sub and 'class="ru-pro-gate"' not in sub)
    check("both upsell buttons removed",
          "Unlock PRO Targets" not in sub and "See Entry, Targets" not in sub)
    check("old mislabelled boxes are gone",
          ">5D TARGET</div>" not in sub and ">TARGET</div>" not in sub)
    print(f"        first banner values: {vals[:10]}")

    print(f"\n=== {'ALL PASS' if not failures else str(len(failures)) + ' FAILURE(S)'} ===")
    for f in failures:
        print(f"   - {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())