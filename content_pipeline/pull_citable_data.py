"""
Pull the LIVE scanner rows this lane can legitimately cite.

Every figure used in an expansion must come from here (scanner output), the
/wins page, or a cited filing. This dumps the rows for the tickers each thin
article discusses, so expansions use real current values rather than memory.
"""
import json
import re
import urllib.request
from pathlib import Path

REPO = Path(r"C:\Users\Tyler_AI\ai-market-cap")


def get(url, timeout=45):
    rq = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(rq, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


home = get("https://aismarketcap.com")
rows = json.loads(re.search(r"rowsData\s*=\s*(\[.*?\]);", home, re.S).group(1))
scanner = {r["ticker"]: r for r in rows}

print(f"scanner universe: {len(rows)} rows")
print("\nsample of available fields:")
print("  " + ", ".join(sorted(rows[0].keys())))

# What the thin articles need.
WANT = {
    "ai-infrastructure (expand)":
        ["NVDA", "VRT", "SMCI", "DELL", "MU", "CRDO", "LITE", "ANET",
         "AVGO", "AMAT", "ETN", "VRT", "CEG", "GEV", "OKLO"],
    "dell / vrt / mu / crdo / smci (expand)":
        ["DELL", "VRT", "MU", "CRDO", "SMCI", "LITE", "ANET", "AMAT"],
    "nbis / amd / meta (expand)":
        ["AMD", "META", "NVDA", "AMZN", "GOOG", "MSFT"],
    "best-ai-stocks / momentum / nov-calendar":
        ["NVDA", "AMD", "AVGO", "MU", "PLTR", "CRDO", "SMCI", "VRT"],
}

for label, tickers in WANT.items():
    print("\n" + "=" * 76)
    print(label)
    print("=" * 76)
    print(f"  {'tkr':<7}{'score':>6}{'earnings':>11}{'days':>6}{'price':>10}"
          f"{'IV':>8}{'pe_up':>8}{'3d':>10}{'short%':>8}")
    for t in tickers:
        r = scanner.get(t)
        if not r:
            print(f"  {t:<7}  -- not in current scanner universe --")
            continue
        print(f"  {t:<7}{str(r.get('score','')):>6}{str(r.get('earnings_date','')):>11}"
              f"{str(r.get('days_left','')):>6}{str(r.get('price','')):>10}"
              f"{str(r.get('iv','')):>8}{str(r.get('pe_upside','')):>8}"
              f"{str(r.get('3d','')):>10}{str(r.get('short_int','')):>8}")

# AI-relevant rows ranked, as a citable set
AI = {"NVDA", "AMD", "AVGO", "MU", "SMCI", "CRDO", "VRT", "LITE", "ANET",
      "AMAT", "DELL", "MRVL", "ARM", "TER", "ONTO", "KLAC", "LRCX", "AMAT",
      "ETN", "GEV", "CEG", "OKLO", "NBIS", "PLTR", "HPE", "APH", "COHR", "GLW"}
ai_rows = sorted([r for r in rows if r["ticker"] in AI],
                 key=lambda r: r.get("score", 0), reverse=True)
print("\n" + "=" * 76)
print(f"AI-INFRA names in scanner, by score ({len(ai_rows)})")
print("=" * 76)
for r in ai_rows:
    print(f"  {r['ticker']:<7}{r.get('score',''):>4}  {r.get('earnings_date',''):>8}"
          f"  {r.get('days_left',''):>3}d left  price {r.get('price','')}"
          f"  IV {r.get('iv','')}")

(REPO / "content_pipeline" / "scanner_snapshot.json").write_text(
    json.dumps(rows, indent=2), encoding="utf-8")
print("\nsaved -> scanner_snapshot.json")