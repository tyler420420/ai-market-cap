#!/usr/bin/env python3
"""
REGRESSION GUARD for the AI earnings scanner output.

Several bugs regressed more than once because nothing checked the generated
HTML, only the Python source. This asserts on the actual generated artifact,
which is what users see.

Run after every scan:
    python verify_output.py

Exit code 0 = all checks pass. Non-zero = at least one regression.
"""
import re
import sys
import os

HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "ai_earnings_today.html")

failures = []
notes = []

# The four trending cards, in render order. One shared style string, so they
# are adjacent and can be sliced apart without parsing HTML.
CARD_LABELS = ("TRENDING IPO", "TRENDING METAL", "TRENDING UTILITY", "TRENDING ETF")

# A card is at most ~400 chars of markup from its label onward. Bounding the
# window keeps the last card (TRENDING ETF, followed by the rest of the page)
# from sweeping up an unrelated <a> from the scanner table below it.
CARD_WINDOW = 600


def card_block(html, label):
    """Markup belonging to one trend card: from its label to the next label.

    Cards are emitted adjacently with one shared style string, so slicing from
    one label to the next isolates a single card. Capped at CARD_WINDOW so the
    final card cannot run on into the scanner table and borrow its anchor.
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

    WHY THIS REPLACED A NAME LIST. The guard used to assert that one of
    "Stripe", "Databricks", "Canva" appeared in the page. Those are FALLBACK
    companies, used only when stockanalysis.com returns an empty calendar. So
    the check passed on the fallback path and FAILED whenever the real scrape
    succeeded and rendered a real company - which is the good outcome. That
    inverted the guard: on 2026-10-21 both daily scans refused to deploy
    perfectly good HTML because the IPO scrape started working.

    The real invariant is structural: a populated card has an anchor with
    non-empty text and a real href. An unpopulated card renders the literal
    string "No data" with no anchor at all (see _trend_card in
    ai_earnings_scanner.py). This catches that without caring whether the
    company came from the scrape or the fallback.
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


def check(name, condition, detail=""):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}" + (f"  -- {detail}" if detail else ""))
        failures.append(f"{name}: {detail}")


def main():
    if not os.path.exists(HTML):
        print(f"FATAL: {HTML} not found")
        return 1

    with open(HTML, encoding="utf-8") as f:
        c = f.read()

    print("=== Score column header ===")
    # 'll' in "Overall" renders as a ligature glyph in Segoe UI that looks like
    # a corrupted character. The header must say "Top Score".
    check('header says "Top<br>Score"',
          "Top<br>Score" in c,
          "found 'Overall<br>Score' instead - the ll ligature bug")
    check('no "Overall Score" header anywhere',
          "Overall<br>Score" not in c,
          "the 'Overall Score' rename reverted")

    print("\n=== Sentiment column ===")
    # The JS renderTable() used to read r.squeeze, which does not exist in
    # rowsData, so every cell rendered as an em-dash.
    check("JS reads r.sentiment", "r.sentiment" in c)
    check("JS does NOT read r.squeeze", "r.squeeze" not in c,
          "r.squeeze is undefined in rowsData -> cells render as em-dash")

    m = re.search(r"var rowsData=(\[.*?\]);", c, re.S)
    rows_txt = m.group(1) if m else ""
    import json
    try:
        rows = json.loads(rows_txt)
    except Exception as e:
        print(f"  FAIL  rowsData parses as JSON -- {e}")
        failures.append("rowsData is not valid JSON")
        rows = []

    check(f"rowsData has >=20 stocks (got {len(rows)})", len(rows) >= 20)

    sentiments = [r.get("sentiment", "") for r in rows]
    populated = [s for s in sentiments if s in ("Positive", "Negative", "Mixed")]
    check(f"sentiment populated on >=80% of rows "
          f"({len(populated)}/{len(rows)})",
          len(rows) > 0 and len(populated) / len(rows) >= 0.8,
          f"only {len(populated)} of {len(rows)} rows have a real sentiment value")

    print("\n=== Mobile card layout ===")
    # JS renderTable() must emit data-label on every <td>, or the mobile CSS
    # `::before { content: attr(data-label) }` renders nothing.
    m2 = re.search(r"function renderTable\(\)\{(.*?)tbody\.innerHTML", c, re.S)
    js_seg = m2.group(1) if m2 else ""
    td_count = js_seg.count("<td")
    dl_count = js_seg.count('data-label=')
    check(f"every JS <td> has data-label ({dl_count}/{td_count})",
          td_count > 0 and dl_count == td_count,
          f"{td_count - dl_count} td(s) missing data-label -> mobile cards break")

    print("\n=== Trending cards ===")
    # Each of the four cards must render a real link. The old check asserted a
    # hardcoded list of FALLBACK company names, so it passed on the fallback
    # path and failed the moment the live scrape worked - blocking good
    # deploys. See card_populated() for the full account.
    empty_cards = []
    for label in CARD_LABELS:
        blk = card_block(c, label)
        if not blk:
            check(f"{label} card present", False, "card label not found at all")
            empty_cards.append(label)
            continue
        ok, why = card_populated(blk)
        check(f"{label} card populated", ok, why)
        if not ok:
            empty_cards.append(label)
    check("all four trending cards populated", not empty_cards,
          f"empty or missing: {', '.join(empty_cards)}")
    # The historical regression this guard exists for: an empty scrape AND a
    # failed fallback used to render a placeholder instead of real companies.
    check("no 'No upcoming IPOs' placeholder", "No upcoming IPOs" not in c,
          "the empty-state placeholder shipped instead of real IPOs")

    print("\n=== Favicon ===")
    # --local mode writes a file:/// path, which browsers refuse to load,
    # so the deployed page loses its tab icon.
    check("favicon link uses /favicon.ico (not file:///)",
          'href="/favicon.ico"' in c and "file:///" not in c,
          "favicon href points at file:/// which browsers block in production")
    check("PNG icon declared (browsers prefer it over ICO)",
          'rel="icon" type="image/png"' in c,
          "only the ICO is declared; Chrome/Safari fall back to a globe")
    check("apple-touch-icon declared",
          'rel="apple-touch-icon"' in c,
          "missing apple-touch-icon - iOS home screen icon will be blank")

    print("\n=== Popup timing ===")
    # Tied to the JS context, not a bare number. A bare "300000" can match any
    # price, offset or coordinate anywhere in the file and pass while the popup
    # timing is wrong entirely. These anchor the number to its function.
    check("popup delay is 5 min (setTimeout 300000)", "},300000);" in c,
          "the popup setTimeout no longer fires at 5 minutes")
    check("popup cooldown is 1 hour (>=3600000)", ">=3600000" in c,
          "the dismissal cooldown comparison is gone or changed")

    print("\n=== Encoding ===")
    check("no UTF-8 mojibake (C3 82 = 'A-circumflex')",
          "\u00c2\u00b1" not in c, "double-encoded plus/minus or em-dash present")
    check("no replacement characters", "\ufffd" not in c)

    print()
    if failures:
        print(f"*** {len(failures)} REGRESSION(S) DETECTED ***")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("=== ALL CHECKS PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())