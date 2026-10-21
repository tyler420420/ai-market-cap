"""Classify every live article: junk (template filler) vs keep (real analysis).
Also check for recorded backlinks pointing at each article — those must be
preserved with a 301 rather than deleted.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\Tyler_AI\Desktop\traffic_machine")
import quality_gate as qg  # noqa: E402

INDEX = Path(r"C:\Users\Tyler_AI\ai-market-cap\blog\index.json")
PUB = Path(r"C:\Users\Tyler_AI\Desktop\traffic_machine\article_queue\published")
TM = Path(r"C:\Users\Tyler_AI\Desktop\traffic_machine")

# Load queued source content where available.
title_map = {}
for j in PUB.glob("*.json"):
    try:
        d = json.loads(j.read_text(encoding="utf-8"))
        title_map[d.get("title", "").strip().lower()] = d
    except Exception:
        pass

# Gather any recorded backlink URLs across traffic_machine state files.
backlinks = set()
for pat in ("*.json", "*.log"):
    for f in TM.glob(pat):
        try:
            txt = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for m in re.finditer(r"https?://(?:www\.)?aismarketcap\.com/blog/([a-z0-9\-]+)", txt, re.I):
            backlinks.add(m.group(1).lower())

print(f"backlink references found in local state/logs: {len(backlinks)}")
for b in sorted(backlinks)[:20]:
    print("   ", b)

articles = json.loads(INDEX.read_text(encoding="utf-8"))
titles = [a["title"] for a in articles]

junk, keep = [], []
for a in articles:
    slug = a["slug"]
    src = title_map.get(a["title"].strip().lower())
    content = src.get("content", "") if src else ""
    typ = "wins" if ("wins" in (a.get("keyword", "") or "").lower()
                     or "this week's top" in a["title"].lower()) else "standard"
    v = qg.evaluate({
        "title": a["title"], "content": content,
        "keyword": a.get("keyword", ""),
        "meta_description": a.get("meta_description", ""),
    }, titles, article_type=typ)
    # Template filler = has a banned phrase OR a spun title pattern
    junky = bool(v["checks"].get("template_hits")) or bool(v["checks"].get("bad_title"))
    rec = {"slug": slug, "title": a["title"], "date": a.get("date"),
           "words": v["checks"].get("word_count", 0), "score": v["score"],
           "reasons": v["reasons"][:2], "has_backlink": slug.lower() in backlinks}
    (junk if junky else keep).append(rec)

print("\n" + "=" * 78)
print(f"KEEP (genuinely written): {len(keep)}")
for r in keep:
    print(f"   {r['date']}  {r['words']:>5}w  {r['title'][:52]}")

print("\n" + "=" * 78)
print(f"JUNK (template filler): {len(junk)}")
for r in junk:
    flag = "  <-- HAS BACKLINK" if r["has_backlink"] else ""
    print(f"   {r['date']}  {r['words']:>5}w  {r['title'][:52]}{flag}")

linked = [r for r in junk if r["has_backlink"]]
print(f"\njunk with backlinks (must 301, not delete): {len(linked)}")
out = Path(r"C:\Users\Tyler_AI\Desktop\traffic_machine\junk_audit.json")
out.write_text(json.dumps({"junk": junk, "keep": keep,
                           "backlinks": sorted(backlinks)}, indent=2), encoding="utf-8")
print(f"saved -> {out}")