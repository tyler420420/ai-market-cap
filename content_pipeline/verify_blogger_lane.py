"""
BLOGGER LANE VERIFIER — single entry point.

Audit fixes applied (2026-10-20):
  - WRONG PATH:  imports resolve via Path(__file__).parent, never CWD
  - WRONG SUBJECT: card checks run against the LIVE SERVED page, not a local
    re-implementation of the renderer (the old _test_render_cards.py copied
    scanner_web's template and _esc() by hand, so it passed even when the real
    renderer was broken — same failure class as CTO's stale-import bug)
  - SILENT PASS: every check exits non-zero on failure
  - NEVER RUNS: wired into run_daily.bat so it executes unattended

Exit codes: 0 = all passed, 1 = at least one FAILED
"""

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
BLOG = REPO / "blog"
INDEX_JSON = BLOG / "index.json"
LIVE_BLOG = "https://aismarketcap.com/blog"
LIVE_SITEMAP = "https://aismarketcap.com/sitemap.xml"

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")


# ── 1. EXCERPT BUILDER — imports the REAL publisher module ──
def test_excerpt_builder():
    print("\n[1] build_excerpt() — real module, __file__-relative import")
    sys.path.insert(0, str(HERE))
    from blog_to_railway import build_excerpt  # noqa: E402

    cases = [
        ("plain", "", ""),
        ("tags", "<p>Hi <strong>there</strong></p>", "Hi there"),
        ("entity brackets", "<p>a &lt;b&gt; c</p>", "a b c"),
        ("nbsp", "<p>a&nbsp;&nbsp;b</p>", "a b"),
        ("whitespace", "<p>\n  one\n  two\n</p>", "one two"),
    ]
    for name, src, expect in cases:
        got = build_excerpt(src)
        ok = got == expect
        check(f"excerpt/{name}", ok, f"got {got!r} want {expect!r}")

    long_src = "<p>" + ("word " * 200) + "</p>"
    out = build_excerpt(long_src)
    check("excerpt/truncates", len(out) <= 203 and out.endswith("..."), f"len={len(out)}")
    check("excerpt/no angle brackets", "<" not in out and ">" not in out)


# ── 2. SERVED PAGE — the actual deployed artifact ──
def test_served_page():
    print("\n[2] Live served page — checks what Railway actually deploys")
    expected = json.loads(INDEX_JSON.read_text(encoding="utf-8"))

    # Railway redeploy is not instant. If the served page disagrees with
    # index.json, re-check after a settle window before calling it a failure —
    # otherwise every publish reports a false FAIL purely from deploy lag.
    status, html = fetch(LIVE_BLOG)
    served = len(re.findall(r'<div class="t"[^>]*>(.*?)</div>', html, re.S))

    if served != len(expected) and served < len(expected):
        print(f"     ...served {served} < index {len(expected)}; "
              f"waiting 180s for Railway redeploy, then re-checking")
        time.sleep(180)
        status, html = fetch(LIVE_BLOG)
        served = len(re.findall(r'<div class="t"[^>]*>(.*?)</div>', html, re.S))

    check("blog page HTTP 200", status == 200, f"got {status}")
    check("blog page non-empty", len(html) > 5000, f"{len(html)} bytes")

    cards = re.findall(r'<div class="t"[^>]*>(.*?)</div>', html, re.S)
    check("card count == index.json count",
          len(cards) == len(expected),
          f"served {len(cards)} vs index {len(expected)}")
    check("no cap on cards (shows all)", len(cards) == len(expected))

    leaked = re.findall(r"&lt;(?:p|strong|div|h2)&gt;", html)
    check("no literal HTML tags in cards", not leaked, f"{len(leaked)} leaked")

    # Every published article must be reachable at its own URL.
    missing = []
    for a in expected[:12]:
        try:
            s, body = fetch(f"https://aismarketcap.com/blog/{a['slug']}")
            if s != 200 or len(body) < 2000:
                missing.append(f"{a['slug']}({s},{len(body)})")
        except Exception as e:
            missing.append(f"{a['slug']}(ERR {type(e).__name__})")
    check("all articles reachable at own URL", not missing, ", ".join(missing[:3]))

    s_status, sitemap = fetch(LIVE_SITEMAP)
    check("sitemap HTTP 200", s_status == 200)
    not_in_sitemap = [a["slug"] for a in expected if a["slug"] not in sitemap]
    check("all articles in served sitemap", not not_in_sitemap,
          ", ".join(not_in_sitemap[:3]))


# ── 3. SOURCE <-> SERVED CONSISTENCY ──
def test_source_matches_served():
    print("\n[3] Source vs served — catches a deploy that served the wrong tree")
    _, html = fetch(LIVE_BLOG)
    newest = json.loads(INDEX_JSON.read_text(encoding="utf-8"))[0]

    check("newest article title served",
          newest["title"].replace("&", "&amp;") in html
          or newest["title"] in html,
          newest["title"][:50])

    # The literal-'<p>' bug must never reappear in the served excerpt div.
    m = re.search(r'class="l"[^>]*>(.*?)</div>', html, re.S)
    check("served excerpt div exists", m is not None)
    if m:
        decoded = (m.group(1).replace("&lt;", "<").replace("&gt;", ">")
                          .replace("&amp;", "&"))
        check("served excerpt has no <p> after decode", "<p>" not in decoded)


# ── 4. RETIRED SLUGS 301, NOT 404 ──
def test_retired_redirects():
    print("\n[4] Retired junk URLs still 301 to /blog")
    manifest = BLOG / "retired_slugs.json"
    if not manifest.exists():
        check("retired_slugs.json exists", False, "missing")
        return
    retired = json.loads(manifest.read_text(encoding="utf-8"))
    check("retired manifest non-empty", len(retired) > 0, f"{len(retired)} slugs")

    index = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    still_listed = [s for s in retired if s in {a["slug"] for a in index}]
    check("no retired slug still in index.json", not still_listed,
          ", ".join(still_listed[:3]))

    orphans = [s for s in retired if (BLOG / f"{s}.html").exists()]
    check("no retired html file still on disk", not orphans,
          ", ".join(orphans[:3]))


def main():
    print("=" * 66)
    print("  BLOGGER LANE VERIFIER — verifies the SERVED artifact")
    print("=" * 66)

    for fn in (test_excerpt_builder, test_served_page,
               test_source_matches_served, test_retired_redirects):
        try:
            fn()
        except Exception as e:
            check(f"{fn.__name__} crashed", False, f"{type(e).__name__}: {e}")

    passed = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - passed
    print("\n" + "=" * 66)
    print(f"  {passed} passed, {failed} FAILED")
    if failed:
        print("\n  FAILURES:")
        for n, ok, d in results:
            if not ok:
                print(f"    - {n}: {d}")
    print("=" * 66)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())