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


def body_from_html(slug):
    """Recover the body from the served page so we regenerate byte-equivalently."""
    html = (BLOG / f"{slug}.html").read_text(encoding="utf-8")
    m = re.search(r'<div class=article-body>(.*?)<div class=cta-box>', html, re.S)
    return m.group(1) if m else None


def fix(slug, meta, dry=False):
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next((a for a in idx if a["slug"] == slug), None)
    if entry is None:
        print(f"[FAIL] not in index: {slug}")
        return 1

    body = body_from_html(slug)
    if body is None:
        print("[FAIL] could not recover body from html")
        return 1

    words = len(re.sub(r"<[^>]+>", " ", body).split())
    print(f"slug   : {slug}")
    print(f"old meta ({len(entry.get('meta_description',''))}c): "
          f"{entry.get('meta_description','')[:90]!r}")
    print(f"new meta ({len(meta)}c): {meta!r}")
    print(f"body preserved: {words} words")
    if not (70 <= len(meta) <= 160):
        print("  [WARN] new meta still outside 70-160")

    if dry:
        print("[dry-run] nothing written")
        return 0

    article = dict(entry)
    article["meta_description"] = meta
    html = btr.build_article_html(article, slug)
    (BLOG / f"{slug}.html").write_text(html, encoding="utf-8")
    entry["meta_description"] = meta
    INDEX.write_text(json.dumps(idx, indent=2, ensure_ascii=False),
                     encoding="utf-8")
    print(f"[OK] {slug}.html regenerated, index.json meta patched")
    return 0


if __name__ == "__main__":
    raise SystemExit(fix(sys.argv[1], sys.argv[2], "--dry-run" in sys.argv))