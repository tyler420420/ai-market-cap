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

    print("\n=== IPO cards ===")
    # These regressed when a scan ran while stockanalysis.com returned an
    # empty calendar AND the fallback list failed to apply. The section
    # rendered its "No upcoming IPOs" placeholder instead of real companies.
    ipo_names = ["Stripe", "Databricks", "Canva"]
    present = [n for n in ipo_names if n in c]
    check(f"IPO cards populated ({len(present)}/3: {', '.join(present)})",
          len(present) >= 1,
          "no IPO companies rendered - fetch returned empty and fallback failed")
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
    check("popup delay is 5 min (300000)", "300000" in c)
    check("popup cooldown is 1 hour (3600000)", "3600000" in c)

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