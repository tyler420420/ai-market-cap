"""
Patch ONLY the meta description of an existing article, preserving its body.

Rewriting the whole article to fix a 165-char meta would risk shortening
content that already meets the word floor. This touches meta only, then
regenerates the HTML with the identical body via build_article_html().

Usage: python fix_meta.py <slug> "<new meta description>"
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(r"C:\Users\Tyler_AI\ai-market-cap")
sys.path.insert(0, str(REPO / "content_pipeline"))
import blog_to_railway as btr  # noqa: E402

BLOG = REPO / "blog"
INDEX = BLOG / "index.json"


def body_from_queue(slug):
    """Recover the body from the QUEUE source, not index.json.

    index.json stores title/meta/keyword but NOT the body. Reading content
    from it and passing it to build_article_html produced an article with an
    empty body - 0 words on the served page. The queue JSON is the source of
    truth for article prose.
    """
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next((a for a in idx if a["slug"] == slug), None)
    title = (entry or {}).get("title", "")

    qdir = REPO / "content_pipeline" / "article_queue"
    best = None
    for f in list(qdir.glob("*.json")) + list((qdir / "published").glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if (d.get("title", "") or "").strip().lower() == title.strip().lower():
            c = d.get("content", "")
            if c and (best is None or len(c) > len(best[1])):
                best = (f, c)
    return best if best else (None, None)


def fix(slug, meta, dry=False):
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next((a for a in idx if a["slug"] == slug), None)
    if entry is None:
        print(f"[FAIL] not in index: {slug}")
        return 1

    src, body = body_from_queue(slug)
    if not body:
        print("[FAIL] could not recover body from queue for this slug")
        return 1

    words = len(re.sub(r"<[^>]+>", " ", body).split())
    print(f"slug   : {slug}")
    print(f"body source: {src.name}")
    print(f"old meta ({len(entry.get('meta_description',''))}c): "
          f"{entry.get('meta_description','')[:90]!r}")
    print(f"new meta ({len(meta)}c): {meta!r}")
    print(f"body words  : {words}")
    if words < 200:
        print("  [ABORT] recovered body looks truncated - refusing to write")
        return 1
    if not (70 <= len(meta) <= 160):
        print("  [WARN] new meta still outside 70-160")

    if dry:
        print("[dry-run] nothing written")
        return 0

    article = dict(entry)
    article["content"] = body
    article["meta_description"] = meta
    html = btr.build_article_html(article, slug)
    (BLOG / f"{slug}.html").write_text(html, encoding="utf-8")
    entry["meta_description"] = meta
    INDEX.write_text(json.dumps(idx, indent=2, ensure_ascii=False),
                     encoding="utf-8")
    print(f"[OK] {slug}.html regenerated ({len(html)} bytes), meta patched")
    return 0


if __name__ == "__main__":
    raise SystemExit(fix(sys.argv[1], sys.argv[2], "--dry-run" in sys.argv))