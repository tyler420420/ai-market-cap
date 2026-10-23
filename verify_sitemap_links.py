"""Audit every URL in the live sitemap and report anything that is not a healthy 200.

WHY THIS EXISTS

Trailing-slash routing is a silent killer here. Flask 404s `/blog/` because the
rule is declared `/blog`, and every crawler, social preview and human-typed URL
uses the trailing slash. The sitemap was correct, so no sitemap check would ever
have caught it - the link was simply absent from the thing being audited.

That is the general shape of the risk: the artifact everyone checks (the
sitemap) was clean while the thing visitors actually hit (/blog/) was a 404. So
this fetches the LIVE sitemap and then fetches every URL it lists, because the
only way to know a link works is to follow it.

Run:  python verify_sitemap_links.py
"""
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

SITE = "https://aismarketcap.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")

# Cloudflare returns 1010 to the default urllib User-Agent, which looks exactly
# like a dead site. Always send a real browser UA.
OPENER = urllib.request.build_opener()
OPENER.addheaders = [("User-Agent", UA)]

# These are expected to fail or redirect by design; flagging them as broken
# every hour would train everyone to ignore the real findings.
EXPECTED_NON_200 = {
    "/logout",          # requires a session cookie
}


def fetch(url, timeout=25):
    req = urllib.request.Request(url)
    try:
        with OPENER.open(req, timeout=timeout) as r:
            return r.getcode(), url, ""
    except urllib.error.HTTPError as e:
        return e.code, url, (e.headers.get("Location") or "")
    except Exception as e:
        return 0, url, "%s: %s" % (type(e).__name__, e)


def main():
    code, url, _ = fetch(SITE + "/sitemap.xml")
    if code != 200:
        print("FAIL  could not read the live sitemap (HTTP %s)" % code)
        return 1
    body = urllib.request.urlopen(
        urllib.request.Request(SITE + "/sitemap.xml", headers={"User-Agent": UA}),
        timeout=25).read().decode("utf-8", "replace")

    locs = re.findall(r"<loc>([^<]+)</loc>", body)
    print("sitemap lists %d URLs - checking each one over HTTP\n" % len(locs))

    results = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        for c, u, extra in ex.map(fetch, locs):
            results.append((c, u, extra))

    bad = []
    for c, u, extra in sorted(results):
        path = u.replace(SITE, "") or "/"
        if c == 200:
            continue
        if path in EXPECTED_NON_200:
            print("NOTE  %s -> HTTP %s (expected)" % (path, c))
            continue
        bad.append((path, c, extra))

    if not bad:
        print("PASS  every sitemap URL returns 200 (%d/%d)" % (len(locs), len(locs)))
    else:
        print("FAIL  %d of %d sitemap URLs are not serving 200:\n" % (len(bad), len(locs)))
        for path, c, extra in bad:
            line = "  %-60s HTTP %s" % (path, c)
            if extra:
                line += "  %s" % extra
            print(line)

    # Trailing-slash tolerance is checked separately and deliberately, because
    # the sitemap is generated from the same route table that serves the pages -
    # so it can be perfectly correct while the shape a visitor types is a 404.
    print("\n--- trailing-slash shape a visitor or crawler actually types ---")
    shapes = ["/blog", "/pricing", "/wins", "/stocks"]
    ts_bad = []
    for shape in shapes:
        c, _, extra = fetch(SITE + shape + "/")
        ok = c == 200
        print("  %-10s %-12s -> HTTP %s%s" % (shape + "/", shape, c,
                                              ("  " + extra) if extra else ""))
        if not ok:
            ts_bad.append(shape + "/")
    if ts_bad:
        print("\nFAIL  %d path(s) 404 with a trailing slash: %s"
              % (len(ts_bad), ", ".join(ts_bad)))
        print("      Every search engine, social preview and hand-typed URL uses")
        print("      the trailing slash. A 404 here hides that page from crawlers")
        print("      even when the sitemap lists it correctly.")
    else:
        print("\nPASS  every major route tolerates a trailing slash")

    return 1 if (bad or ts_bad) else 0


if __name__ == "__main__":
    sys.exit(main())