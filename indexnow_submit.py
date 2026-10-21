#!/usr/bin/env python3
"""
Submit new/changed URLs to search engines via IndexNow.

WHY THIS EXISTS
---------------
The old anonymous sitemap pings are dead:
    google.com/ping  -> 404 "Sitemaps ping is deprecated" (retired 2023)
    bing.com/ping    -> 410 Gone

So generate_stock_pages.py --ping could never have worked, even if that cron
had actually fired. IndexNow is the supported replacement: free, no API key,
no OAuth, instant notification to Bing and its partners (Yandex, Seznam,
Naver, DuckDuckGo).

Google has no equivalent public endpoint. Its sitemap discovery path is
Search Console (needs OAuth) plus the `Sitemap:` line in robots.txt - which
aismarketcap.com already serves. So Google coverage is handled by robots.txt,
not by a ping.

Usage:
    python indexnow_submit.py                 # submit URLs changed since last run
    python indexnow_submit.py --all           # submit every URL in the sitemap
    python indexnow_submit.py --dry-run       # print the payload, send nothing

Exit code is always 0 unless the script itself cannot run: a rejected or
unreachable endpoint must never break the caller.
"""
import argparse
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parent
KEY_FILE = REPO / "indexnow_key.txt"
STATE_FILE = REPO / ".indexnow_state.json"
INDEXNOW_URL = "https://api.indexnow.org/indexnow"
HOST = "aismarketcap.com"
BLOG_INDEX = REPO / "blog" / "index.json"
STOCK_PAGES = REPO / "stock_pages"


def load_key():
    if not KEY_FILE.exists():
        return None
    return KEY_FILE.read_text(encoding="utf-8").strip() or None


def load_state():
    if not STATE_FILE.exists():
        return {"urls": []}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return {"urls": data.get("urls", [])}
    except Exception:
        return {"urls": []}


def save_state(urls):
    STATE_FILE.write_text(json.dumps({"urls": sorted(urls)}), encoding="utf-8")


def current_urls():
    """Every URL we consider ours: stock pages + live blog articles."""
    urls = set()

    if STOCK_PAGES.is_dir():
        for p in STOCK_PAGES.glob("*.html"):
            urls.add(f"https://{HOST}/stock/{p.stem}")

    if BLOG_INDEX.exists():
        try:
            articles = json.loads(BLOG_INDEX.read_text(encoding="utf-8"))
        except Exception:
            articles = []
        retired = set()
        rp = REPO / "blog" / "retired_slugs.json"
        if rp.exists():
            try:
                d = json.loads(rp.read_text(encoding="utf-8"))
                retired = set(d.keys()) if isinstance(d, dict) else set(d)
            except Exception:
                pass
        for a in articles:
            if isinstance(a, dict):
                slug = a.get("slug")
                if slug and slug not in retired:
                    urls.add(f"https://{HOST}/blog/{slug}")

    urls.add(f"https://{HOST}/")
    urls.add(f"https://{HOST}/blog")
    return urls


def submit(key, urls, dry_run=False):
    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": f"https://{HOST}/indexnow_key.txt",
        # IndexNow caps a single request at 10,000 URLs; we send far fewer.
        "urlList": sorted(urls)[:10000],
    }
    body = json.dumps(payload).encode("utf-8")

    if dry_run:
        print(f"INDEXNOW (dry-run): {len(payload['urlList'])} urls, "
              f"key={key[:8]}..., host={HOST}")
        for u in payload["urlList"][:10]:
            print(f"    {u}")
        if len(payload["urlList"]) > 10:
            print(f"    ... and {len(payload['urlList']) - 10} more")
        return True

    req = urllib.request.Request(
        INDEXNOW_URL, data=body, method="POST",
        headers={"Content-Type": "application/json; charset=utf-8",
                 "User-Agent": "AIScannerBot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            code = r.status
        # 200/202 both mean accepted. 403 = key rejected, 422 = bad payload.
        ok = code in (200, 201, 202)
        print(f"INDEXNOW: HTTP {code} - {'submitted' if ok else 'REJECTED'} "
              f"({len(payload['urlList'])} urls)")
        return ok
    except urllib.error.HTTPError as e:
        # 400/403/422 are "your submission was not accepted" - log, never raise.
        print(f"INDEXNOW: HTTP {e.code} {e.reason} - not submitted "
              f"(check key file is served at /indexnow_key.txt)")
        return False
    except Exception as e:
        print(f"INDEXNOW: endpoint unreachable ({e}) - continuing")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true",
                    help="submit every known URL, not just changed ones")
    ap.add_argument("--dry-run", action="store_true",
                    help="show the payload without sending")
    args = ap.parse_args()

    key = load_key()
    if not key:
        print("INDEXNOW: no key found - run generate_indexnow_key first "
              "(submission skipped, not an error)")
        return 0

    all_urls = current_urls()
    if args.all:
        changed = all_urls
    else:
        seen = set(load_state()["urls"])
        changed = all_urls - seen

    print(f"INDEXNOW: {len(all_urls)} known urls, {len(changed)} new/changed")

    if not changed:
        print("INDEXNOW: nothing new to submit")
        save_state(all_urls)
        return 0

    ok = submit(key, changed, dry_run=args.dry_run)
    # Record what we know about either way, so a failed submission is retried
    # tomorrow only for URLs that are still not present on the next run.
    if ok or args.dry_run:
        save_state(all_urls)
    else:
        print("INDEXNOW: state not advanced - changed urls will retry next run")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"INDEXNOW: unexpected error ({e}) - skipping, not fatal")
        sys.exit(0)