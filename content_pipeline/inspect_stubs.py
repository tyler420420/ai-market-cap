"""Inspect the three stub articles from the local git tree (they 404 live —
which is itself a finding)."""
import json
import re
from pathlib import Path

REPO = Path(r"C:\Users\Tyler_AI\ai-market-cap")
idx = json.loads((REPO / "blog" / "index.json").read_text(encoding="utf-8"))

STUBS = [
    "bili-was-this-weeks-top-pre-earnings-pick-heres-the-setup",
    "ddog-was-this-weeks-top-pre-earnings-pick-heres-the-setup",
    "ai-infrastructure-stocks-the-pre-earnings-play-nobody-is-talking-about",
]

# Which stub html files actually exist on disk?
for slug in STUBS:
    print("=" * 74)
    f = REPO / "blog" / f"{slug}.html"
    print(f"SLUG : {slug}")
    print(f"html on disk : {f.exists()}")
    entry = next((a for a in idx if a["slug"] == slug), None)
    print(f"in index.json: {entry is not None}")
    if entry:
        print(f"title  : {entry['title']}")
        print(f"date   : {entry['date']}")
        print(f"stored meta ({len(entry.get('meta_description',''))}c): "
              f"{entry.get('meta_description','')[:120]!r}")
    if f.exists():
        html = f.read_text(encoding="utf-8")
        m = re.search(r'<div class="?article-body"?>(.*?)</div>', html, re.S)
        body = m.group(1).split("cta-box")[0] if m else ""
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()
        print(f"body words: {len(txt.split())}")
        print(f"body head : {txt[:500]}")
    else:
        print("  (no html file — index entry is orphaned)")
    print()

# Also check /wins for BILI / DDOG coverage
print("=" * 74)
print("WINS PAGE — are BILI / DDOG already documented there?")
print("=" * 74)
try:
    import urllib.request
    rq = urllib.request.Request("https://aismarketcap.com/wins",
                                headers={"User-Agent": "Mozilla/5.0"})
    wins = urllib.request.urlopen(rq, timeout=30).read().decode("utf-8", "replace")
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", wins))
    for t in ("BILI", "DDOG", "INOD", "SNOW", "OKTA"):
        print(f"  {t:<6} on /wins: {t in text}")
    i = text.find("BILI")
    if i > 0:
        print(f"\n  BILI context: {text[max(0,i-140):i+240]}")
except Exception as e:
    print(f"  could not read /wins: {e}")