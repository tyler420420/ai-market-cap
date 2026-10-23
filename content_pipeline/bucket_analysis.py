"""Build the A/B/C bucket evidence table for the 14 short articles.

Facts only, all pulled live at run time:
  - served article text (tickers + the setup language used)
  - live scanner universe membership
  - live price / 5d move for tickers that LEFT the universe

Run:  python bucket_analysis.py
"""
import json
import re
import urllib.request
from pathlib import Path

BASE = "https://aismarketcap.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def get(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


# ---------- live scanner universe ----------
home = get(BASE + "/")
rows = json.loads(re.search(r"rowsData\s*=\s*(\[.*?\]);", home, re.S).group(1))
scanner = {}
for r in rows:
    scanner[r["ticker"].upper()] = {
        "score": r.get("score"), "earnings": r.get("earnings_date"),
        "days": r.get("days_left"), "price": r.get("price"),
        "iv": r.get("iv"), "pe_up": r.get("pe_upside"),
        "sector": r.get("sector"), "company": r.get("company_name"),
    }

# ---------- served articles ----------
articles = json.loads(get(BASE + "/blog/index.json"))
SHORT_TARGET = 1200

STOP = {"THE", "AND", "FOR", "YOU", "THIS", "WITH", "FROM", "THAT", "WHAT",
        "ARE", "NOT", "ITS", "HAS", "HOW", "NOW", "ONE", "OUT", "GET", "AI"}

# Tickers these articles plausibly discuss, for BARE-word detection.
KNOWN_AI = ["SMCI", "DELL", "MU", "CRDO", "LITE", "AVGO", "META", "GEV",
            "OKLO", "IBM", "TSLA", "LRCX", "NBIS", "AMD", "VRT", "NVDA",
            "ANET", "AMAT", "ETN", "CEG", "KLAC", "PLTR", "MSFT", "GOOG",
            "AMZN", "INTC", "QCOM", "MRVL", "ARM", "ORCL", "SOUN", "APLD"]

results = []
for a in articles:
    slug = a["slug"]
    html = get(f"{BASE}/blog/{slug}")
    m = re.search(r'<div class="?article-body"?>(.*?)</div>', html, re.S)
    body = m.group(1) if m else ""
    text = re.sub(r"<[^>]+>", " ", body)

    words = len([w for w in re.findall(r"[A-Za-z0-9$%.'-]+", text)
                 if any(c.isalnum() for c in w)])

    tickers = sorted({t for t in re.findall(r"\$([A-Z]{2,5})\b", body)
                      if t not in STOP})
    # Also catch BARE uppercase tickers ("MU", "Dell") - the $ prefix is rare
    # in these articles, and missing them makes a departed ticker look present.
    for cand in KNOWN_AI:
        if re.search(rf"\b{cand}\b", body):
            tickers.append(cand)
    tickers = sorted(set(t for t in tickers if t not in STOP))
    in_sc = [t for t in tickers if t in scanner]
    out_sc = [t for t in tickers if t not in scanner]

    # setup language = still-framed-as-forward-looking
    setup_words = len(re.findall(
        r"\b(watch|into the print|days left|before earnings|setup|thesis|"
        r"catalyst|what to watch|position)\b", text, re.I))
    past_words = len(re.findall(
        r"\b(reported|printed|results|beat|missed|after the print|"
        r"already closed|has closed|actual)\b", text, re.I))

    results.append({
        "slug": slug, "title": a["title"], "date": a["date"], "words": words,
        "h2": [re.sub(r"<[^>]+>", "", h).strip()
               for h in re.findall(r"<h2[^>]*>(.*?)</h2>", body, re.S)],
        "tickers": tickers, "in_scanner": in_sc, "out_of_scanner": out_sc,
        "setup_lang": setup_words, "past_lang": past_words,
        "short": words < SHORT_TARGET,
    })

# ---------- live prices for tickers that left the universe ----------
need = sorted({t for r in results for t in r["out_of_scanner"]})
live = {}
for t in need:
    try:
        j = json.loads(get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{t}"
            "?range=1mo&interval=1d"))
        res = j["chart"]["result"][0]
        meta = res["meta"]
        closes = [c for c in res["indicators"]["quote"][0]["close"] if c]
        px = closes[-1] if closes else None
        prev = closes[-2] if len(closes) > 1 else None
        d1 = ((px / prev - 1) * 100) if px and prev else None
        m5 = ((px / closes[-6] - 1) * 100) if px and len(closes) > 6 else None
        live[t] = {
            "price": round(px, 2) if px else None,
            "name": meta.get("shortName"),
            "d1_pct": round(d1, 2) if d1 else None,
            "m1_pct": round(m5, 2) if m5 else None,
            "currency": meta.get("currency"),
        }
    except Exception as e:
        live[t] = {"error": str(e)}

out = Path(__file__).with_name("bucket_analysis.json")
out.write_text(json.dumps({"articles": results, "live_departed": live,
                           "scanner_universe": scanner}, indent=1),
               encoding="utf-8")

# ---------- report ----------
short = [r for r in results if r["short"]]
short.sort(key=lambda r: r["words"])

print("=" * 78)
print(f"SHORT ARTICLES ({len(short)} of {len(results)}), worst first")
print("=" * 78)
for r in short:
    print(f"\n{r['words']:>5}w  {r['slug']}")
    print(f"        {r['title']}")
    print(f"        in scanner : {r['in_scanner'] or '-'}")
    print(f"        LEFT       : {r['out_of_scanner'] or '-'}")
    print(f"        lang       : {r['setup_lang']} setup / {r['past_lang']} past")
    for h in r["h2"]:
        print(f"          - {h[:66]}")
    for t in r["out_of_scanner"]:
        d = live.get(t, {})
        if "error" in d:
            print(f"        live {t}: ERROR {d['error'][:50]}")
        else:
            print(f"        live {t}: ${d['price']}  1d {d['d1_pct']}%  "
                  f"1mo {d['m1_pct']}%  ({d['name']})")

print()
print("=" * 78)
print("Citable AI names still IN the scanner universe")
print("=" * 78)
for t, s in sorted(scanner.items(), key=lambda x: -(x[1]["score"] or 0)):
    if s["sector"] and "AI" in str(s["company"] or "") or t in (
            "NVDA", "ANET", "AMZN", "GOOG", "MSFT", "AMAT", "AMD", "VRT",
            "CEG", "ETN", "PLTR", "KLAC"):
        print(f"  {t:<6} score {s['score']:<4} {s['earnings']} ({s['days']}d)  "
              f"${s['price']}  IV {s['iv']}  pe_up {s['pe_up']}  {s['company']}")

print(f"\nsaved -> {out.name}")