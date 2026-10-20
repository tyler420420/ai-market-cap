#!/usr/bin/env python3
"""
FULL SITE AUDIT - checks the LIVE deployed site, not the local source.

Every regression in this project shared one signature: the Python source was
correct but the shipped artifact was stale. Source-level checks never caught
it. This script audits https://aismarketcap.com/ over HTTP, so it fails when
the deployment drifts from the code - which is the failure that actually
reached users.

Exit 0 = clean. Exit 1 = at least one failure.

    python audit_live.py
"""
import json
import re
import sys
import urllib.request
import urllib.error

BASE = "https://aismarketcap.com"
TIMEOUT = 30

failures = []
warnings = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   -- {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(f"{name}: {detail}")


def warn(name, detail=""):
    print(f"  WARN  {name}" + (f"   -- {detail}" if detail else ""))
    warnings.append(name)


def get(path):
    req = urllib.request.Request(BASE + path,
                                 headers={"User-Agent": "Mozilla/5.0 site-audit"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.status, r.read(), dict(r.headers)


def main():
    # ---------- 1. every route returns 200 ----------
    print("=== Route availability ===")
    routes = ["/", "/pricing", "/about", "/blog", "/wins", "/calendar",
              "/stocks", "/account", "/login", "/robots.txt", "/sitemap.xml",
              "/favicon.ico", "/static/logo.png",
              "/stock/NVDA", "/stock/GOOG", "/wins/panw"]
    bodies = {}
    for p in routes:
        try:
            code, body, _ = get(p)
            bodies[p] = body
            check(f"{p} -> 200", code == 200, f"got {code}")
        except urllib.error.HTTPError as e:
            check(f"{p} -> 200", False, f"HTTP {e.code}")
        except Exception as e:
            check(f"{p} -> 200", False, str(e)[:70])

    home = bodies.get("/", b"").decode("utf-8", "replace")

    # ---------- 2. the table ----------
    print("\n=== Scanner table ===")
    check("viewport meta tag present",
          'name="viewport"' in home and "width=device-width" in home)
    check("table#stockTable exists", 'id="stockTable"' in home)

    check("score header says 'Top Score'", "Top<br>Score" in home,
          "'Overall Score' is back - the Segoe UI ll-ligature glyph")
    check("no 'Overall Score' anywhere", "Overall<br>Score" not in home)

    m = re.search(r"var rowsData=(\[.*?\]);", home, re.S)
    rows = []
    if m:
        try:
            rows = json.loads(m.group(1))
        except Exception as e:
            check("rowsData parses as JSON", False, str(e)[:60])
    check("rowsData parses and has >=20 stocks", len(rows) >= 20,
          f"got {len(rows)}")

    # sentiment
    if rows:
        sent = [r.get("sentiment", "") for r in rows]
        good = [s for s in sent if s in ("Positive", "Negative", "Mixed")]
        check(f"sentiment populated ({len(good)}/{len(rows)})",
              len(rows) > 0 and len(good) / len(rows) >= 0.8,
              f"only {len(good)} of {len(rows)} rows carry a real value")
    check("JS reads r.sentiment", "r.sentiment" in home)
    check("JS does NOT read r.squeeze", "r.squeeze" not in home,
          "r.squeeze is undefined -> every sentiment cell renders as an em-dash")
    check("sentiment label is 'Sentiment' not 'Trend'",
          'data-label="Trend"' not in home,
          "static rows still use the old 'Trend' label")

    # ---------- 3. mobile card layout ----------
    print("\n=== Mobile card layout ===")
    m2 = re.search(r"function renderTable\(\)\{(.*?)tbody\.innerHTML", home, re.S)
    js = m2.group(1) if m2 else ""
    tds, dls = js.count("<td"), js.count("data-label=")
    check(f"every JS td has data-label ({dls}/{tds})",
          tds > 0 and dls == tds, f"{tds - dls} td(s) missing data-label")
    check("mobile media query present", "max-width:768px" in home or "max-width: 768px" in home)

    # ---------- 4. sorting ----------
    print("\n=== Sorting ===")
    check("initial sort is score descending",
          "sortCol='ticker'" in home and "sortBy('score')" in home,
          "score-desc-on-load marker missing")
    check("sort arrows render as real glyphs",
          ("\\u25b2" in home or "\u25b2" in home or "\\u25bc" in home or "\u25bc" in home),
          "triangle sort arrows missing/mojibake")

    # ---------- 5. IPO + ETF ----------
    print("\n=== IPO & trending ETF ===")
    ipo_hits = [n for n in ("Stripe", "Databricks", "Canva") if n in home]
    check(f"IPO cards populated ({len(ipo_hits)}/3)", len(ipo_hits) >= 1,
          "no IPO companies rendered")
    check("no 'No upcoming IPOs' placeholder", "No upcoming IPOs" not in home)
    check("trending ETF card rendered", "TRENDING ETF" in home)

    # ---------- 6. favicon ----------
    print("\n=== Favicon ===")
    fm = re.search(r'<link[^>]*rel="icon"[^>]*>', home)
    check("favicon link tag present", fm is not None)
    if fm:
        check("favicon href is /favicon.ico", 'href="/favicon.ico"' in fm.group(0),
              fm.group(0)[:90])
        check("no file:/// favicon in production",
              "file:///" not in fm.group(0), "local-mode path leaked into deploy")
    check("PNG icon declared", 'rel="icon" type="image/png"' in home,
          "ICO-only declaration; Chrome/Safari may fall back to a globe")
    check("apple-touch-icon declared", 'rel="apple-touch-icon"' in home,
          "missing apple-touch-icon")
    for icon_path in ("/favicon.ico", "/favicon.png", "/apple-touch-icon.png"):
        try:
            code, body, hdrs = get(icon_path)
            check(f"{icon_path} serves icon bytes", code == 200 and len(body) > 300,
                  f"status={code} bytes={len(body)}")
        except Exception as e:
            check(f"{icon_path} serves icon bytes", False, str(e)[:60])

    # ---------- 7. subscription popup ----------
    print("\n=== Subscription popup ===")
    check("popup delay is 5 minutes (300000)", "300000" in home)
    check("popup cooldown is 1 hour (3600000)", "3600000" in home)
    check("dismissal stored in localStorage", "sub_popup_dismissed_at" in home)
    check("popup hidden from subscribers", "__isSubscriber" in home)

    # ---------- 8. encoding ----------
    print("\n=== Encoding ===")
    check("no mojibake (A-circumflex sequences)", "\u00c2" not in home,
          "double-encoded characters present")
    check("no replacement characters", "\ufffd" not in home)

    # ---------- 9. fresh data ----------
    print("\n=== Data freshness ===")
    dates = set(re.findall(r"Generated\s+([A-Z][a-z]+ \d{1,2}, \d{4})", home))
    dates |= set(re.findall(r"Data (?:fresh|as of)[^0-9]*(\d{4}-\d{2}-\d{2})", home))
    if dates:
        print(f"  info  page dates: {sorted(dates)}")
    else:
        warn("no generated-date stamp found on page")
    check("at least 3 stocks with score >= 80",
          len([r for r in rows if r.get("score", 0) >= 80]) >= 3)

    # ---------- summary ----------
    print()
    if warnings:
        print(f"{len(warnings)} warning(s)")
    if failures:
        print(f"*** {len(failures)} FAILURE(S) ***")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("=== LIVE SITE AUDIT CLEAN ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())