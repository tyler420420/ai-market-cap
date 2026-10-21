"""
Fix existing blog index excerpts — strip HTML to plain text.

The old publisher pre-escaped excerpts to &lt;p&gt; and the index page rendered
them raw, so every card showed a literal "<p>". This rebuilds every excerpt
from the stored plain text (un-escaping first, then trimming) so index.json
matches the new build_excerpt() contract.
"""

import html as _html
import json
import re
from pathlib import Path

INDEX_FILE = Path(r"C:\Users\Tyler_AI\ai-market-cap\blog\index.json")
_WS_RE = re.compile(r"\s+")


def build_excerpt(content, limit=200):
    """Mirror of blog_to_railway.build_excerpt, operating on stored text."""
    text = _html.unescape(content or "")
    text = text.replace("<p>", " ").replace("</p>", " ")
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("<", " ").replace(">", " ")
    text = _WS_RE.sub(" ", text).strip()
    if len(text) > limit:
        cut = text[:limit].rsplit(" ", 1)[0]
        text = cut.rstrip(" ,;:-") + "..."
    return text


def main():
    if not INDEX_FILE.exists():
        print("[FAIL] index.json not found")
        return 1

    index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    changed = 0

    for entry in index:
        old = entry.get("excerpt", "") or ""
        new = build_excerpt(old)
        if new != old:
            entry["excerpt"] = new
            changed += 1
            print(f"  [FIX] {entry.get('slug', '?')}")
            print(f"        {new[:96]}")

    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OK] Repaired {changed}/{len(index)} excerpts -> {INDEX_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())