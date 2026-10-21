#!/usr/bin/env python3
"""
Reconcile blog/index.json against the actual blog/*.html files.

sitemap.xml is built from blog/index.json, so an article HTML that exists but
has no index entry is invisible to Google and Bing. New articles are written
by the daily article generator in a separate lane; this script only makes sure
whatever landed on disk is actually discoverable.

Rules:
  - never remove entries (a missing file is not proof the article is gone)
  - never invent content: title/description/keyword are parsed out of the page
  - never index ai_earnings_today.html - that is scanner output, not an article
  - idempotent: running twice adds nothing the second time

Prints:  SYNC: <n> entries, <k> added, <j> already present
"""
import datetime
import json
import re
import sys
from pathlib import Path

BLOG = Path(__file__).resolve().parent / "blog"
INDEX = BLOG / "index.json"
RETIRED = BLOG / "retired_slugs.json"
NOT_AN_ARTICLE = "ai_earnings_today.html"


def load_retired():
    """Slugs of purged template-filler articles.

    19 low-quality posts were removed from the index on purpose and now 301 to
    /blog. If their HTML is ever regenerated on disk we must NOT re-index them -
    that would silently undo the purge and put junk back in front of search
    engines. Retire is permanent.
    """
    if not RETIRED.exists():
        return set()
    try:
        data = json.loads(RETIRED.read_text(encoding="utf-8"))
    except Exception:
        return set()
    if isinstance(data, dict):
        return set(data.keys())
    if isinstance(data, list):
        return set(data)
    return set()


def field(text, pattern):
    m = re.search(pattern, text, re.S | re.I)
    return m.group(1).strip() if m else ""


def main():
    if not BLOG.is_dir():
        print("SYNC: no blog/ directory, skipping")
        return 0
    if not INDEX.exists():
        print("SYNC: index.json missing, skipping (not creating it here)")
        return 0

    try:
        idx = json.loads(INDEX.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"SYNC: cannot parse index.json ({e}), skipping")
        return 0
    if not isinstance(idx, list):
        print("SYNC: index.json is not a list, skipping")
        return 0

    have = {e.get("slug") for e in idx if isinstance(e, dict)}
    retired = load_retired()
    files = [p for p in sorted(BLOG.glob("*.html")) if p.name != NOT_AN_ARTICLE]
    skipped_retired = [p.stem for p in files if p.stem in retired]
    files = [p for p in files if p.stem not in retired]

    added = []
    for p in files:
        if p.stem in have:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        title = field(text, r"<title>(.*?)</title>") or p.stem.replace("-", " ").title()
        desc = field(text, r'name="description"\s+content="([^"]*)"')
        kw = field(text, r'name="keywords"\s+content="([^"]*)"')
        idx.append({
            "slug": p.stem,
            "title": title[:200],
            "keyword": kw or p.stem.replace("-", " ").title(),
            "date": datetime.date.today().isoformat(),
            "meta_description": (desc or title)[:300],
            "excerpt": (desc or title)[:200],
        })
        added.append(p.stem)

    if added:
        try:
            INDEX.write_text(json.dumps(idx, indent=2, ensure_ascii=False),
                             encoding="utf-8")
        except Exception as e:
            print(f"SYNC: failed to write index.json ({e})")
            return 0
        print(f"SYNC: {len(idx)} entries, {len(added)} added: {', '.join(added)}")
    else:
        msg = f"SYNC: {len(idx)} entries, 0 added ({len(files)} article files, all indexed)"
        if skipped_retired:
            msg += f"; {len(skipped_retired)} purged slug(s) left retired"
        print(msg)

    return 0


if __name__ == "__main__":
    sys.exit(main())