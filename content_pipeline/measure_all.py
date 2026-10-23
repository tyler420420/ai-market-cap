"""
Measure every article from the SERVED page — word count + meta description.
Google reads what the server returns, so local files are not evidence.

Also reports which tickers currently appear in the live scanner, so we only
cite figures we can actually source.
"""
import json
import re
import urllib.request
from pathlib import Path

REPO = Path(r"C:\Users\Tyler_AI\ai-market-cap")
idx = json.loads((REPO / "blog" / "index.json").read_text(encoding="utf-8"))


def get(url, timeout=40):
    rq = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(rq, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")


# live scanner universe
_, home = get("https://aismarketcap.com")
rows = json.loads(re.search(r"rowsData\s*=\s*(\[.*?\]);", home, re.S).group(1))
scanner = {r["ticker"]: r for r in rows}

print("=" * 104)
print(f"{'slug':<46}{'words':>6}{'meta':>6}  {'ticker':<6}{'inScanner':<10}")
print("=" * 104)

results = []
for a in idx:
    slug = a["slug"]
    st, html = get(f"https://aismarketcap.com/blog/{slug}")

    m = re.search(r'<div class="?article-body"?>(.*?)</div>', html, re.S)
    body = m.group(1) if m else ""
    body = body.split("cta-box")[0]
    text = re.sub(r"<[^>]+>", " ", body)
    words = len([w for w in re.findall(r"[A-Za-z0-9$%.'-]+", text)
                 if any(c.isalnum() for c in w)])

    # meta description AS SERVED
    mm = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
                   html, re.I | re.S)
    served_meta = (mm.group(1).strip() if mm else "")

    tickers = sorted(set(re.findall(r"\$([A-Z]{2,5})\b", body)))
    primary = tickers[0] if tickers else ""
    insc = primary in scanner if primary else False

    results.append({
        "slug": slug, "title": a["title"], "date": a["date"],
        "words": words, "meta": served_meta, "meta_len": len(served_meta),
        "ticker": primary, "in_scanner": insc, "all_tickers": tickers,
        "stored_meta": a.get("meta_description", ""),
    })

    flag = ""
    if words < 1200:
        flag += " SHORT"
    if served_meta and not (70 <= len(served_meta) <= 160):
        flag += " META"
    if not served_meta:
        flag += " NOMETA"
    print(f"{slug[:46]:<46}{words:>6}{len(served_meta):>6}  {primary:<6}{str(insc):<10}{flag}")

print()
short = [r for r in results if r["words"] < 1200]
bad_meta = [r for r in results if r["meta"] and not (70 <= r["meta_len"] <= 160)]
dupes = {}
for r in results:
    if r["meta"]:
        dupes.setdefault(r["meta"], []).append(r["slug"])

print("=" * 104)
print(f"SUMMARY over {len(results)} served articles")
print(f"  under 1200 words      : {len(short)}")
for r in short:
    print(f"      {r['words']:>5}w  {r['slug'][:52]}")
print(f"  meta outside 70-160   : {len(bad_meta)}")
for r in bad_meta:
    print(f"      {r['meta_len']:>4}c  {r['slug'][:46]}")
print(f"  duplicate meta values :")
for k, v in dupes.items():
    if len(v) > 1:
        print(f"      {len(v)}x  {k[:60]!r}  -> {v}")

out = REPO / "content_pipeline" / "measure_all_articles.json"
out.write_text(json.dumps(results, indent=2), encoding="utf-8")
print(f"\nsaved -> {out.name}")

print("\nscanner coverage for stub tickers:")
for r in short:
    t = r["ticker"]
    if t and t in scanner:
        s = scanner[t]
        print(f"  {t}: earnings={s.get('earnings_date')} score={s.get('score')} "
              f"price={s.get('price')} iv={s.get('iv')}")
    else:
        print(f"  {t or '?'}: NOT in current scanner universe "
              f"(tickers mentioned: {r['all_tickers']})")