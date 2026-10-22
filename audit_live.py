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

# The four trending cards, in render order. Shared with verify_output.py - the
# same inverted-guard bug lived in both files, so both were fixed together.
CARD_LABELS = ("TRENDING IPO", "TRENDING METAL", "TRENDING UTILITY", "TRENDING ETF")

# A card is at most ~400 chars of markup from its label onward. Capped so the
# last card cannot run on into the scanner table and borrow its anchor.
CARD_WINDOW = 600


def card_block(html, label):
    """Markup belonging to one trend card: from its label to the next label.

    Cards are emitted adjacently with one shared style string, so slicing from
    one label to the next isolates a single card without parsing HTML.
    """
    i = html.find(label)
    if i < 0:
        return ""
    rest = html[i + len(label):]
    stops = [p for p in (rest.find(l) for l in CARD_LABELS) if p >= 0]
    nxt = min(stops) if stops else CARD_WINDOW
    return rest[:min(nxt, CARD_WINDOW)]


def card_populated(block):
    """True when a card renders a real company/symbol link.

    The previous check asserted that "Stripe", "Databricks" or "Canva"
    appeared in the page. Those are FALLBACK companies, used only when the
    IPO calendar scrape returns nothing - so the check passed on the fallback
    path and failed whenever the real scrape succeeded. The invariant is
    structural instead: a populated card has an anchor with non-empty text
    and a real href; an unpopulated one renders "No data" with no anchor.
    """
    m = re.search(r'<a\s[^>]*href="([^"]*)"[^>]*>([^<]*)</a>', block)
    if not m:
        return False, "no anchor rendered (card rendered its empty state)"
    href, text = m.group(1).strip(), m.group(2).strip()
    if not text or text.lower() in ("no data", "n/a", "-", "tbd"):
        return False, f"anchor text is {text!r}"
    if not href or href.startswith("#") or href.lower().startswith("javascript"):
        return False, f"anchor href is {href!r}"
    return True, f"{text} -> {href}"


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

    # ---------- 5. trending cards ----------
    print("\n=== Trending cards ===")
    # Structural check, not a fallback-name list. See card_populated().
    #
    # NOTE ON REPORTING. This audits the LIVE site, so when the deployed build
    # predates the four gold cards every label is missing at once. That is one
    # root cause, not four bugs, so it is reported as a single failure. The
    # per-card lines are diagnostic detail printed underneath, not extra
    # failures - otherwise one stale build buries real problems in noise.
    missing, unpopulated = [], []
    for label in CARD_LABELS:
        blk = card_block(home, label)
        if not blk:
            print(f"        {label}: label not present in the live HTML")
            missing.append(label)
            continue
        ok, why = card_populated(blk)
        print(f"        {label}: {why}")
        if not ok:
            unpopulated.append(label)
    all_bad = missing + unpopulated
    check("four trending cards rendered and populated", not all_bad,
          ("live build predates the trending cards (missing: "
           + ", ".join(missing) + ")" if missing else
           "card rendered its empty state (empty: " + ", ".join(unpopulated) + ")"))
    check("no 'No upcoming IPOs' placeholder", "No upcoming IPOs" not in home)

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
    check("popup delay is 5 minutes (setTimeout 300000)", "},300000);" in home,
          "the popup setTimeout no longer fires at 5 minutes")
    check("popup cooldown is 1 hour (>=3600000)", ">=3600000" in home,
          "the dismissal cooldown comparison is gone or changed")
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