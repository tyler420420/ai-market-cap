"""
TASK 3: which angle types produce distinct content vs padding?

Two questions I can answer with data:
  1. Volume per angle_type
  2. Near-duplicate detection - are multiple articles the same piece with a
     different ticker? That is the real "padding" test.

What I CANNOT answer: which angles rank. That needs Search Console data, which
is not connected. I will not guess.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(r"C:\Users\Tyler_AI\ai-market-cap")
sys.path.insert(0, str(REPO / "content_pipeline"))
import quality_gate as qg  # noqa: E402

idx = json.loads((REPO / "blog" / "index.json").read_text(encoding="utf-8"))
recent = [a for a in idx if a["date"] >= "2026-10-20"]

print("=" * 70)
print(f"ANGLE MIX — {len(recent)} recent articles")
print("=" * 70)

angles = Counter()
titles = []
for a in recent:
    kw = (a.get("keyword") or "").lower()
    f = REPO / "blog" / f"{a['slug']}.html"
    body = ""
    if f.exists():
        html = f.read_text(encoding="utf-8")
        m = re.search(r'<div class="?article-body"?>(.*?)</div>', html, re.S)
        if m:
            body = re.sub(r"<[^>]+>", " ", m.group(1))
    # infer angle from the title pattern
    t = a["title"].lower()
    if "vs peers" in t:
        ang = "ticker_vs"
    elif "why is" in t:
        ang = "ticker_move"
    elif "earnings date" in t or "earnings:" in t:
        ang = "ticker_earnings"
    elif "earnings calendar" in t:
        ang = "sector_roundup"
    elif "pre-earnings setup" in t:
        ang = "ticker_setup"
    else:
        ang = "other"
    angles[ang] += 1
    words = re.sub(r"\s+", " ", body).lower().split()
    titles.append((a["slug"], a["title"], ang, set(words)))

for ang, n in angles.most_common():
    print(f"  {ang:<18} {n}")

# ── near-duplicate detection: token Jaccard on article bodies ──
print()
print("=" * 70)
print("NEAR-DUPLICATE CHECK (Jaccard overlap on body word sets)")
print("=" * 70)
pairs = []
for i in range(len(titles)):
    for j in range(i + 1, len(titles)):
        s1, s2 = titles[i][3], titles[j][3]
        if not s1 or not s2:
            continue
        inter = len(s1 & s2)
        union = len(s1 | s2)
        jac = inter / union if union else 0
        if jac > 0.25:
            pairs.append((jac, titles[i][1], titles[j][1]))

pairs.sort(reverse=True)
if pairs:
    for jac, t1, t2 in pairs[:12]:
        print(f"  {jac:.0%}  {t1[:40]:<42} | {t2[:40]}")
else:
    print("  no pairs above 25% overlap")

print()
print("=" * 70)
print("SHARED-SENTENCE CHECK — identical sentences across articles")
print("=" * 70)
sent = {}
for slug, title, ang, words in titles:
    f = REPO / "blog" / f"{slug}.html"
    if not f.exists():
        continue
    html = f.read_text(encoding="utf-8")
    m = re.search(r'<div class="?article-body"?>(.*?)</div>', html, re.S)
    if not m:
        continue
    text = re.sub(r"<[^>]+>", " ", m.group(1))
    for s in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text)):
        s = s.strip().lower()
        if len(s.split()) >= 12:
            sent.setdefault(s, []).append(slug)

dupes = {s: sl for s, sl in sent.items() if len(set(sl)) > 1}
if dupes:
    for s, sl in list(dupes.items())[:10]:
        print(f"  in {len(set(sl))} articles: {s[:90]}...")
    print(f"\n  {len(dupes)} sentences appear in more than one article")
else:
    print("  no shared sentences of 12+ words across articles")