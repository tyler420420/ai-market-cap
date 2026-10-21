"""Verify the 4 trending cards by executing the REAL source block from
ai_earnings_scanner.py against the real ipo_etf_data.json.

Why exec the extracted text instead of a copy: a copy proves the copy works.
Extracting the shipped lines proves the file we will deploy is correct.
"""
import json
import re
import sys
import textwrap
from pathlib import Path

REPO = Path(r"C:\Users\Tyler_AI\ai-market-cap")
src = (REPO / "ai_earnings_scanner.py").read_text(encoding="utf-8")

START = "    _CARD_CSS = ("
END = "ipo_card_html += '</div>'"
i = src.index(START)
j = src.index(END, i) + len(END)
block = textwrap.dedent(src[i:j])
print(f"extracted {len(block)} chars of shipped source\n")

ns = {"ipo_etf_data": {}, "real_ipos": []}
# Feed the same locals main() builds.
data = json.loads((REPO / "ipo_etf_data.json").read_text(encoding="utf-8"))
ns["ipo_etf_data"] = data
ns["real_ipos"] = data.get("ipos", [])[:3]
ns["trending"] = data.get("trending_etf") or {}
ns["top_metal"] = data.get("top_metal") or {}
ns["top_utility"] = data.get("top_utility") or {}
ns["ipo_card_html"] = ""

exec(block, ns)
out = ns["ipo_card_html"]

print("--- checks ---")
fails = 0
for label in ("TRENDING IPO", "TRENDING METAL", "TRENDING UTILITY", "TRENDING ETF"):
    ok = label in out
    print(("PASS" if ok else "FAIL"), f"card label present: {label}")
    fails += (not ok)

# Uniformity: every card must share ONE style signature, and there must be
# exactly 4 of them. A per-card override is exactly the bug we are fixing.
card_divs = re.findall(r'<div style="([^"]*flex:1 1 0[^"]*)"', out)
print(("PASS" if len(card_divs) == 4 else "FAIL"),
      f"exactly 4 uniformly-styled cards (found {len(card_divs)})")
fails += (len(card_divs) != 4)
print(("PASS" if len(set(card_divs)) == 1 else "FAIL"),
      f"all cards share one identical style string ({len(set(card_divs))} distinct)")
fails += (len(set(card_divs)) != 1)

# Gold everywhere: no legacy green/blue/purple card styling survives.
for stale in ("#2ea043", "#1f6feb", "#5741d9", "#9333ea", "margin-left:48px"):
    bad = stale in out
    print(("PASS" if not bad else "FAIL"), f"legacy style removed: {stale}")
    fails += bad

gold = out.count("#ffd700")
print(("PASS" if gold >= 8 else "FAIL"), f"gold applied across cards ({gold} refs)")
fails += (gold < 8)

# Real data, not placeholders.
for cat, key in (("METAL", "top_metal"), ("UTILITY", "top_utility"), ("ETF", "trending_etf")):
    t = (data.get(key) or {}).get("ticker")
    ok = bool(t) and t in out
    print(("PASS" if ok else "FAIL"), f"{cat} shows real ticker {t!r}")
    fails += (not ok)

print("\n--- rendered ---")
print(re.sub(r' style="[^"]*"', ' style=".."', out)[:900])
print(f"\n=== {'ALL PASS' if fails == 0 else str(fails) + ' FAILURES'} ===")
sys.exit(1 if fails else 0)