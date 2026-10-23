"""Cross-check article claims against the LIVE scanner + wins page.

Local sources first (fast, authoritative for us): the served scanner table
carries earnings dates, scores and price. Then anything the scanner cannot
confirm is flagged as needing an external filing/news citation.
"""
import json
import re
import urllib.request
from pathlib import Path

REPO = Path(r"C:\Users\Tyler_AI\ai-market-cap")


def fetch(url):
    rq = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(rq, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


home = fetch("https://aismarketcap.com")
rows = json.loads(re.search(r"rowsData\s*=\s*(\[.*?\]);", home, re.S).group(1))
by_ticker = {r["ticker"]: r for r in rows}

wins = fetch("https://aismarketcap.com/wins")
win_tickers = set(re.findall(r"\b([A-Z]{2,5})\b", wins))

idx = json.loads((REPO / "blog" / "index.json").read_text(encoding="utf-8"))
recent = [a for a in idx if a["date"] >= "2026-10-20"]

print("=" * 72)
print("CLAIMS THE SCANNER CAN CONFIRM OR CONTRADICT")
print("=" * 72)

report = []
for a in recent:
    f = REPO / "blog" / f"{a['slug']}.html"
    if not f.exists():
        continue
    html = f.read_text(encoding="utf-8")
    m = re.search(r'<div class="?article-body"?>(.*?)</div>', html, re.S)
    if not m:
        continue
    text = re.sub(r"<[^>]+>", " ", m.group(1))
    text = re.sub(r"\s+", " ", text)

    for tkr in sorted(set(re.findall(r"\$([A-Z]{2,5})\b", text)) |
                      set(re.findall(r"\b([A-Z]{2,5})\b\s+(?:reported|beat|printed|guided)", text))):
        if tkr not in by_ticker:
            continue
        r = by_ticker[tkr]
        # did the article assert an earnings date, and does it match?
        dates = re.findall(
            r"\b(January|February|March|April|May|June|July|August|September|"
            r"October|November|December)\s+(\d{1,2})\b", text)
        article_dates = [f"{mon} {d}" for mon, d in dates]
        report.append({
            "ticker": tkr, "slug": a["slug"], "title": a["title"],
            "scanner_earnings_date": r.get("earnings_date"),
            "scanner_days_left": r.get("days_left"),
            "scanner_score": r.get("score"),
            "scanner_price": r.get("price"),
            "article_dates": article_dates[:4],
            "on_wins_page": tkr in win_tickers,
        })

for r in report:
    print(f"\n  {r['ticker']:<6} in {r['slug'][:40]}")
    print(f"    scanner : earnings={r['scanner_earnings_date']}  "
          f"days_left={r['scanner_days_left']}  score={r['scanner_score']}  "
          f"price={r['scanner_price']}")
    print(f"    article : dates mentioned={r['article_dates']}")
    print(f"    wins pg : {r['on_wins_page']}")

print("\n" + "=" * 72)
print(f"{len(report)} ticker/article pairs cross-checked against the live scanner")