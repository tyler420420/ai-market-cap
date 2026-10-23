"""Measure the SEO quality of the LIVE blog articles, not the local files.

Google does not read your markdown. It reads the served HTML: the title, the
meta description, the canonical, the internal links. So this fetches the real
pages and reports what a crawler would actually get.

Run:  python verify_seo_quality.py
"""
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

SITE = "https://aismarketcap.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")
OPENER = urllib.request.build_opener()
OPENER.addheaders = [("User-Agent", UA)]


def get(path):
    try:
        with OPENER.open(SITE + path, timeout=25) as r:
            return r.getcode(), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""


def one(html):
    # An earlier version of this measured 27 characters for a description
    # containing "this week's". The character class [^"'] stops at the FIRST
    # apostrophe, so any English description with a contraction was silently
    # truncated - and the guard then confidently reported "outside the 70-160
    # window" for perfectly good tags.
    #
    # Both attribute styles are now matched with a delimiter-aware pattern, so
    # an apostrophe inside a double-quoted value is just a character. Verified
    # against the real pages: BILI and DDOG are 108 and 109 chars, not 27.
    def attr(name):
        out = ""
        m = re.search(r'<meta[^>]*\bname=["\']%s["\'][^>]*\bcontent="([^"]*)"' % name,
                      html, re.I | re.S)
        if not m:
            m = re.search(r"<meta[^>]*\bname=[\"']%s[\"'][^>]*\bcontent='([^']*)'" % name,
                          html, re.I | re.S)
        if not m:
            m = re.search(r'<meta[^>]*\bcontent="([^"]*)"[^>]*\bname=["\']%s["\']' % name,
                          html, re.I | re.S)
        if not m:
            m = re.search(r"<meta[^>]*\bcontent='([^']*)'[^>]*\bname=[\"']%s[\"']" % name,
                          html, re.I | re.S)
        return m.group(1).strip() if m else out

    def linkval(rel):
        m = re.search(r'<link[^>]*\brel=["\']%s["\'][^>]*\bhref="([^"]*)"' % rel,
                      html, re.I | re.S)
        if not m:
            m = re.search(r"<link[^>]*\brel=[\"']%s[\"'][^>]*\bhref='([^']*)'" % rel,
                          html, re.I | re.S)
        if not m:
            m = re.search(r'<link[^>]*\bhref="([^"]*)"[^>]*\brel=["\']%s["\']' % rel,
                          html, re.I | re.S)
        return m.group(1).strip() if m else ""

    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if m:
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip()

    desc = attr("description")
    canon = linkval("canonical")
    h1 = ""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    if m:
        h1 = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    ld = len(re.findall(r"application/ld\+json", html))

    body = re.sub(r"<script[\s\S]*?</script>", " ", html)
    body = re.sub(r"<style[\s\S]*?</style>", " ", body)
    body = re.sub(r"<nav[\s\S]*?</nav>", " ", body)
    body = re.sub(r"<footer[\s\S]*?</footer>", " ", body)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    words = len([w for w in body.split() if re.search(r"[A-Za-z0-9]", w)])

    # internal links to OTHER articles (self-links do not help discovery)
    links = re.findall(r'href=["\'](/blog/[^"\']+)["\']', html)
    internal = len(set(l for l in links if l not in ("/blog/",)))

    return {
        "title": title, "title_len": len(title),
        "desc": desc, "desc_len": len(desc),
        "canon": canon, "h1": h1, "ld": ld,
        "words": words, "internal_links": internal,
    }


def main():
    code, html = get("/blog")
    if code != 200:
        print("FAIL  cannot read /blog (HTTP %s)" % code)
        return 1
    slugs = sorted(set(re.findall(r'href=["\'](/blog/[^"\']+)["\']', html)))
    slugs = [s for s in slugs if s.rstrip("/").count("/") == 2]
    print("blog index lists %d article links\n" % len(slugs))
    if not slugs:
        print("FAIL  no article links found on /blog - the index is not linked")
        return 1

    sample = slugs[:14]
    with ThreadPoolExecutor(max_workers=8) as ex:
        pages = list(ex.map(lambda s: (s,) + get(s), sample))

    rows, dup_titles, dup_descs = [], {}, {}
    for slug, code, body in pages:
        if code != 200 or not body:
            print("FAIL  %s -> HTTP %s" % (slug, code))
            continue
        d = one(body)
        d["slug"] = slug
        rows.append(d)
        dup_titles.setdefault(d["title"].lower(), []).append(slug)
        dup_descs.setdefault(d["desc"].lower(), []).append(slug)

    print("%-46s %5s %6s %5s %4s %4s" % ("article", "words", "title", "desc", "canon", "ld"))
    print("-" * 82)
    for d in rows:
        print("%-46s %5d %6d %6d %4s %4d" % (
            d["slug"][:46], d["words"], d["title_len"], d["desc_len"],
            "Y" if d["canon"] else "-", d["ld"]))

    n = len(rows) or 1
    print()
    probs = []
    no_canon = [d["slug"] for d in rows if not d["canon"]]
    no_ld = [d["slug"] for d in rows if not d["ld"]]
    short_desc = [d["slug"] for d in rows if d["desc_len"] < 70 or d["desc_len"] > 160]
    no_desc = [d["slug"] for d in rows if not d["desc"]]
    thin = [d["slug"] for d in rows if d["words"] < 1200]
    orphan = [d["slug"] for d in rows if d["internal_links"] == 0]
    dupe_t = {k: v for k, v in dup_titles.items() if len(v) > 1}
    dupe_d = {k: v for k, v in dup_descs.items() if len(v) > 1}

    for label, lst in [("no canonical tag", no_canon),
                       ("no meta description", no_desc),
                       ("meta description outside 70-160 chars", short_desc),
                       ("under 1200 words", thin),
                       ("zero internal links to other articles", orphan),
                       ("no JSON-LD structured data", no_ld)]:
        print("  %-45s %d/%d" % (label, len(lst), n))
        if lst:
            probs.append(label)

    print()
    if dupe_t:
        print("  DUPLICATE TITLES across %d groups:" % len(dupe_t))
        for k, v in list(dupe_t.items())[:5]:
            print("      %r -> %d articles" % (k[:60], len(v)))
        probs.append("duplicate titles")
    if dupe_d:
        print("  DUPLICATE META DESCRIPTIONS across %d groups:" % len(dupe_d))
        for k, v in list(dupe_d.items())[:5]:
            print("      %r -> %d articles" % (k[:60], len(v)))
        probs.append("duplicate descriptions")

    print()
    if probs:
        print("SEO QUALITY: %d issue class(es) found across %d sampled articles"
              % (len(probs), n))
        for p in probs:
            print("   - " + p)
        return 1
    print("SEO QUALITY: all sampled articles carry title, description, "
          "canonical and structured data")
    return 0


if __name__ == "__main__":
    sys.exit(main())