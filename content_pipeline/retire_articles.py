"""
Retire articles to the 301 pattern already proven by retired_slugs.json.

Removes the article from index.json (which also drops it from sitemap.xml and
the blog index), deletes the generated HTML, and records the slug in
retired_slugs.json so /blog/<slug> 301s to /blog instead of 404ing.

Reversible: git has the content, and the slug is in retired_slugs.json.
"""
import json
import sys
from pathlib import Path

REPO = Path(r"C:\Users\Tyler_AI\ai-market-cap")
BLOG = REPO / "blog"
INDEX = BLOG / "index.json"
MANIFEST = BLOG / "retired_slugs.json"

REASON = {
    "bili-was-this-weeks-top-pre-earnings-pick-heres-the-setup":
        "268-word weekly template post duplicating /wins content; ticker no "
        "longer in the scanner universe, so it cannot be honestly expanded to "
        "1200+ with citable current data",
    "ddog-was-this-weeks-top-pre-earnings-pick-heres-the-setup":
        "268-word weekly template post; identical structure to the BILI post "
        "and the result is already documented on /wins",
}


def retire(slugs, dry_run=False):
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    manifest = {}
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    before = len(index)
    to_drop = [a for a in index if a["slug"] in slugs]

    print(f"index.json: {before} articles")
    for a in to_drop:
        print(f"  DROP {a['slug']}")
    for s in slugs:
        if s not in {a['slug'] for a in to_drop}:
            print(f"  WARN not found in index: {s}")

    if dry_run:
        print("\n[dry-run] nothing written")
        return 0
    if not to_drop:
        print("nothing to do")
        return 0

    keep = [a for a in index if a["slug"] not in slugs]

    removed = 0
    for a in to_drop:
        f = BLOG / f"{a['slug']}.html"
        if f.exists():
            f.unlink()
            removed += 1
        manifest[a["slug"]] = REASON.get(a["slug"], "retired")

    INDEX.write_text(json.dumps(keep, indent=2, ensure_ascii=False),
                     encoding="utf-8")
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    print(f"\n[OK] removed {removed} html file(s)")
    print(f"[OK] index.json: {before} -> {len(keep)}")
    print(f"[OK] retired_slugs.json now has {len(manifest)} entries")
    return 0


if __name__ == "__main__":
    # Filter the flag FIRST, then fall back — otherwise `--dry-run` alone is
    # treated as the target list and nothing matches.
    dry = "--dry-run" in sys.argv[1:]
    targets = [t for t in sys.argv[1:] if t != "--dry-run"] or list(REASON)
    raise SystemExit(retire(targets, dry))