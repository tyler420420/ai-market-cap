"""Get the real slug list + the SERVED meta descriptions for the stubs."""
import json
import re
import urllib.request
from pathlib import Path

REPO = Path(r"C:\Users\Tyler_AI\ai-market-cap")
idx = json.loads((REPO / "blog" / "index.json").read_text(encoding="utf-8"))

print("=== full slugs in index.json (for the stub titles) ===")
for a in idx:
    if "infrastructure" in a["slug"] or a["slug"].startswith(("bili-", "ddog-")):
        print(f"  {a['date']}  {len(a['slug'])}c  {a['slug']}")
        print(f"        title: {a['title']}")

print("\n=== SERVED meta descriptions ===")
for a in idx:
    if a["slug"].startswith(("bili-", "ddog-")) or "infrastructure" in a["slug"]:
        rq = urllib.request.Request(f"https://aismarketcap.com/blog/{a['slug']}",
                                     headers={"User-Agent": "Mozilla/5.0"})
        h = urllib.request.urlopen(rq, timeout=30).read().decode("utf-8", "replace")
        m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
                      h, re.I | re.S)
        served = m.group(1).strip() if m else "(none)"
        print(f"\n  slug : {a['slug'][:56]}")
        print(f"  served meta ({len(served)}c): {served!r}")
        print(f"  stored meta ({len(a.get('meta_description',''))}c): "
              f"{a.get('meta_description','')[:100]!r}")

print("\n=== where does the served 27-char meta come from? ===")
a = next(x for x in idx if x["slug"].startswith("bili-"))
rq = urllib.request.Request(f"https://aismarketcap.com/blog/{a['slug']}",
                             headers={"User-Agent": "Mozilla/5.0"})
h = urllib.request.urlopen(rq, timeout=30).read().decode("utf-8", "replace")
for mm in re.finditer(r'<meta[^>]*>', h):
    if "description" in mm.group(0).lower() or "og:" in mm.group(0).lower():
        print("  " + mm.group(0)[:160])