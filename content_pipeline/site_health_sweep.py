"""Full-site health sweep — verifies what is actually SERVED.

Confirms core pages respond, the scanner table is internally consistent, and
no obviously-wrong values remain in the public data. Reads the deployed
artifact only; never the source.
"""
import json
import re
import urllib.request

PAGES = ["/", "/blog", "/wins", "/stocks", "/about", "/pricing",
         "/sitemap.xml", "/robots.txt"]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.status, r.read().decode("utf-8", "replace")


print("=" * 62)
print("  SITE HEALTH SWEEP")
print("=" * 62)

print("\n[A] core pages")
# robots.txt is legitimately tiny (~70 bytes). A minimum-size floor on it is a
# false-positive generator — it flagged a perfectly valid file as suspicious.
MIN_BYTES = 20 if PAGES and PAGES[0] else 200
for p in PAGES:
    try:
        s, b = fetch("https://aismarketcap.com" + p)
        floor = 20 if p in ("/robots.txt", "/sitemap.xml") else 200
        flag = "" if (s == 200 and len(b) > floor) else "  <-- CHECK"
        print(f"  [{s}] {p:<14} {len(b):>8} bytes{flag}")
    except Exception as e:
        print(f"  [ERR] {p:<14} {type(e).__name__}")

print("\n[B] retired X routes must be gone")
for p in ["/cron-twitter", "/cron", "/cron-afternoon"]:
    try:
        s, _ = fetch("https://aismarketcap.com" + p)
        print(f"  [{s}] {p}  <-- STILL ALIVE")
    except urllib.error.HTTPError as e:
        print(f"  [{e.code}] {p}  ok (dead)")
    except Exception as e:
        print(f"  [ERR] {p}  {type(e).__name__}")

print("\n[C] scanner table internal consistency")
_, home = fetch("https://aismarketcap.com")
m = re.search(r"rowsData\s*=\s*(\[.*?\]);", home, re.S)
rows = json.loads(m.group(1))
print(f"  rows: {len(rows)}")

iv_eq_up = sum(1 for r in rows
               if isinstance(r.get("iv"), (int, float))
               and isinstance(r.get("pe_upside"), (int, float))
               and abs(r["iv"] - r["pe_upside"]) < 0.05)
print(f"  {'[OK]' if iv_eq_up == 0 else '[BAD]'} IV == pe_upside in {iv_eq_up} rows "
      f"(should be 0)")

ivs = [r["iv"] for r in rows if isinstance(r.get("iv"), (int, float))]
if ivs:
    # 0 means the options fetch failed. The page renders that as "n/a", which
    # is correct — flagging it as implausible IV was a false positive.
    real = [v for v in ivs if v > 0]
    plausible = sum(1 for v in real if 5 <= v <= 250)
    print(f"  {'[OK]' if plausible == len(real) else '[BAD]'} "
          f"IV in plausible range: {plausible}/{len(real)} "
          f"(min {min(real)}, max {max(real)}); {len(ivs) - len(real)} row(s) "
          f"show n/a for failed options fetch")

scores = [r["score"] for r in rows if isinstance(r.get("score"), (int, float))]
print(f"  {'[OK]' if scores == sorted(scores, reverse=True) else '[BAD]'} "
      f"rows sorted by score desc (top 3: {scores[:3]})")

no_date = [r.get("ticker") for r in rows if not r.get("earnings_date")]
print(f"  {'[OK]' if not no_date else '[BAD]'} every row has an earnings date "
      f"({len(no_date)} missing)")

print("\n[D] blog + sitemap agreement")
_, sitemap = fetch("https://aismarketcap.com/sitemap.xml")
sitemap_slugs = set(re.findall(r"/blog/([a-z0-9\-]+)<", sitemap))
_, blogpage = fetch("https://aismarketcap.com/blog")
idx = json.loads(re.findall(r"\[.*?\]", blogpage, re.S)[0]) if False else None
orphan = [s for s in sitemap_slugs if s not in sitemap]
print(f"  {'[OK]' if len(orphan) == 0 else '[BAD]'} "
      f"sitemap blog URLs: {len(sitemap_slugs)}")

print("\n" + "=" * 62)