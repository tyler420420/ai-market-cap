"""TASK 1 evidence: did the 10/22 articles actually publish and get indexed?

Checks the served URL per article, and whether each is present in the
IndexNow state file (which records what has been submitted to Bing).
"""
import json
import urllib.request
from pathlib import Path

REPO = Path(r"C:\Users\Tyler_AI\ai-market-cap")
idx = json.loads((REPO / "blog" / "index.json").read_text(encoding="utf-8"))
state = json.loads((REPO / ".indexnow_state.json").read_text(encoding="utf-8"))
submitted = set(state.get("urls", []))

print("=== articles dated 10/21 and 10/22: live + submitted? ===")
for a in idx:
    if a["date"] not in ("2026-10-21", "2026-10-22"):
        continue
    url = "https://aismarketcap.com/blog/" + a["slug"]
    try:
        rq = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(rq, timeout=30) as r:
            st, n = r.status, len(r.read())
    except Exception as e:
        st, n = "ERR", type(e).__name__
    mark = "SUBMITTED" if url in submitted else "MISSING"
    print(f"  [{str(st):>3}] {str(n):>7}  idx={mark:<9} {a['title'][:46]}")

print()
print("=== articles dated 10/23 ===")
n23 = [a for a in idx if a["date"] == "2026-10-23"]
print(f"  count: {len(n23)}")
for a in n23:
    print(f"    {a['title'][:52]}")
if not n23:
    print("  (the 07:00 cron for 10/23 has not fired yet - it is 03:56 PT)")

print()
print("=== IndexNow state totals ===")
print(f"  urls recorded as submitted: {len(submitted)}")
blog_slugs = [a["slug"] for a in idx]
not_sub = [s for s in blog_slugs
           if ("https://aismarketcap.com/blog/" + s) not in submitted]
print(f"  live blog articles NOT in IndexNow state: {len(not_sub)}")
for s in not_sub:
    print(f"    {s}")