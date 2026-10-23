"""
Update an EXISTING article in place: body, meta description, title.

blog_to_railway.py only creates articles from the queue, so a rewrite of an
existing post has no path. This regenerates the HTML with that module's own
build_article_html() (so the template stays identical to every other article)
and patches the index.json entry.

Does NOT touch scanner_web.py. Reads/writes blog/*.html and blog/index.json.

Usage:
    python update_article.py <slug> <payload.json>
"""
import json
import sys
from pathlib import Path

REPO = Path(r"C:\Users\Tyler_AI\ai-market-cap")
sys.path.insert(0, str(REPO / "content_pipeline"))

import blog_to_railway as btr  # noqa: E402

BLOG = REPO / "blog"
INDEX = BLOG / "index.json"


def update(slug, payload, dry_run=False):
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next((a for a in idx if a["slug"] == slug), None)
    if entry is None:
        print(f"[FAIL] slug not in index.json: {slug}")
        return 1

    # Preserve original date/author unless the payload overrides them.
    article = {
        "title": payload.get("title", entry.get("title")),
        "meta_description": payload.get("meta_description",
                                        entry.get("meta_description", "")),
        "content": payload.get("content", entry.get("content", "")),
        "keyword": payload.get("keyword", entry.get("keyword", "")),
        "client": "aismarketcap",
        "date": payload.get("date", entry.get("date")),
        "author": payload.get("author", entry.get("author", "AI Market Cap")),
    }

    words = len(article["content"].split())
    meta_len = len(article["meta_description"])

    print(f"slug        : {slug}")
    print(f"title       : {article['title']}")
    print(f"words       : {words}")
    print(f"meta        : {meta_len} chars")
    if not (70 <= meta_len <= 160):
        print(f"  [WARN] meta outside Google's 70-160 window")

    if dry_run:
        print("[dry-run] nothing written")
        return 0

    html = btr.build_article_html(article, slug)
    (BLOG / f"{slug}.html").write_text(html, encoding="utf-8")

    entry["title"] = article["title"]
    entry["meta_description"] = article["meta_description"]
    entry["keyword"] = article["keyword"]
    INDEX.write_text(json.dumps(idx, indent=2, ensure_ascii=False),
                     encoding="utf-8")

    print(f"[OK] regenerated {slug}.html ({len(html)} bytes)")
    print("[OK] index.json entry updated")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    slug = sys.argv[1]
    payload = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    raise SystemExit(update(slug, payload, "--dry-run" in sys.argv))