"""
Re-measure meta descriptions correctly.

The earlier regex was non-greedy up to a quote CHARACTER, so it terminated at
the apostrophe in "this week's" and reported 27 chars. The real served value
is present in full. Same flaw produced the "identical 27-character meta" and
"3 characters" findings — both were measurement artifacts, not site defects.
"""
import html as htmlmod
import json
import re
import urllib.request
from pathlib import Path

REPO = Path(r"C:\Users\Tyler_AI\ai-market-cap")
idx = json.loads((REPO / "blog" / "index.json").read_text(encoding="utf-8"))


def served_meta(page):
    """Proper meta parse: capture until the closing quote that precedes '>'."""
    m = re.search(r'<meta\s+name=["\']description["\']\s+content="(.*?)"\s*/?>',
                  page, re.I | re.S)
    if m:
        return htmlmod.unescape(m.group(1).strip())
    m = re.search(r"<meta\s+name=[\"']description[\"']\s+content='(.*?)'\s*/?>",
                  page, re.I | re.S)
    if m:
        return htmlmod.unescape(m.group(1).strip())
    return ""


rows = []
for a in idx:
    rq = urllib.request.Request(f"https://aismarketcap.com/blog/{a['slug']}",
                                 headers={"User-Agent": "Mozilla/5.0"})
    h = urllib.request.urlopen(rq, timeout=35).read().decode("utf-8", "replace")
    m = re.search(r'<div class="?article-body"?>(.*?)</div>', h, re.S)
    body = (m.group(1).split("cta-box")[0]) if m else ""
    txt = re.sub(r"<[^>]+>", " ", body)
    words = len([w for w in re.findall(r"[A-Za-z0-9$%.'-]+", txt)
                 if any(c.isalnum() for c in w)])
    rows.append({
        "slug": a["slug"], "title": a["title"], "date": a["date"],
        "words": words, "meta": served_meta(h),
        "stored_meta": a.get("meta_description", ""),
    })

print("=" * 100)
print(f"{'slug':<48}{'words':>6}{'metaLen':>9}  status")
print("=" * 100)
short, badmeta = [], []
seen = {}
for r in rows:
    ml = len(r["meta"])
    inrange = 70 <= ml <= 160
    flags = []
    if r["words"] < 1200:
        flags.append("SHORT")
        short.append(r)
    if not inrange:
        flags.append("META")
        badmeta.append(r)
    if r["meta"]:
        seen.setdefault(r["meta"], []).append(r["slug"])
    print(f"{r['slug'][:48]:<48}{r['words']:>6}{ml:>9}  {','.join(flags) or 'ok'}")

print()
print(f"under 1200 words : {len(short)}")
print(f"meta outside 70-160: {len(badmeta)}")
for r in badmeta:
    print(f"    {len(r['meta'])}c  {r['slug'][:50]}")
    print(f"        {r['meta']!r}")

print("\nDUPLICATE served metas:")
dups = {k: v for k, v in seen.items() if len(v) > 1}
if dups:
    for k, v in dups.items():
        print(f"  {len(v)}x {k[:70]!r} -> {v}")
else:
    print("  none - every article has a distinct served meta description")

(REPO / "content_pipeline" / "measure_all_corrected.json").write_text(
    json.dumps(rows, indent=2), encoding="utf-8")
print("\nsaved -> measure_all_corrected.json")