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

# Quote line format Tyler specified:
#   KGC $23.64 · +0.38% 5d   -- one line, middot separator, SIGNED percent.
# The sign is the whole point, so assert '+' actually renders.
signed = re.findall(r'>([+-]\d+\.\d+)% 5d</span>', out)
print(("PASS" if signed else "FAIL"), f"percent rendered with explicit sign ({signed})")
fails += (not signed)
print(("PASS" if out.count("&middot;") == 3 else "FAIL"),
      f"middot separator on all 3 quoted cards ({out.count('&middot;')}/3)")
fails += (out.count("&middot;") != 3)
# Direction must be tinted, and must reuse the ticker strip's own palette
# rather than inventing a second set of colours on the same page.
print(("PASS" if "#00ff88" in out else "FAIL"), "up colour matches .ticker-up (#00ff88)")
fails += ("#00ff88" not in out)

# NEGATIVE PATH: a falling card must show a minus sign AND the down colour.
# Not covered by live data today (all three happen to be up), so drive it
# through the same shipped source with a forced-down fixture.
ns2 = {"ipo_etf_data": {}, "real_ipos": []}
ns2["real_ipos"] = []
ns2["trending"] = {"ticker": "CPER", "price": 5.42, "change_5d": -1.08}
ns2["top_metal"] = {"ticker": "CPER", "price": 5.42, "change_5d": -1.08}
ns2["top_utility"] = None
ns2["ipo_card_html"] = ""
exec(block, ns2)
neg = ns2["ipo_card_html"]
neg_pct = re.findall(r'>([+-]\d+\.\d+)% 5d</span>', neg)
neg_ok = (neg_pct == ["-1.08", "-1.08"]      # metal + etf, both the forced-down fixture
          and "#ff6b6b" in neg               # down colour
          and "#00ff88" not in neg)          # and NOT the up colour
print(("PASS" if neg_ok else "FAIL"),
      f"falling card shows '-' and down colour only (pct={neg_pct})")
fails += (not neg_ok)

# A card with no data must NOT fabricate a price or a 0.00% move.
ns3 = {"ipo_etf_data": {}, "real_ipos": []}
ns3["real_ipos"] = []
ns3["trending"] = {}
ns3["top_metal"] = None
ns3["top_utility"] = None
ns3["ipo_card_html"] = ""
exec(block, ns3)
none_out = ns3["ipo_card_html"]
clean = "+0.00%" not in none_out and "-0.00%" not in none_out and "No data" in none_out
print(("PASS" if clean else "FAIL"), "empty category shows placeholder, never a fake 0.00%")
fails += (not clean)
# No empty <div></div> left behind where a quote line would have gone.
print(("PASS" if '"></div></div>' not in out else "FAIL"), "no empty quote div emitted")
fails += ('"></div></div>' in out)

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