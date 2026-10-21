"""Functional test for the visitor counter in scanner_web.py.

Boots the real Flask app with a test client and drives real requests through
the before_request hook, so this exercises the shipped code path rather than a
copy of the logic.

Run:  python verify_visitor_counter.py
Exit 0 = all checks passed.
"""

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).parent / "scanner_web.py"

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  -- {detail}" if detail and not cond else ""))


# Import scanner_web from an isolated copy so the test never mutates the real
# repo state file (visitor_counts.json / visitor_baseline.json).
with tempfile.TemporaryDirectory() as td:
    tmp_src = Path(td) / "scanner_web.py"
    tmp_src.write_text(SRC.read_text(encoding="utf-8"), encoding="utf-8")

    spec = importlib.util.spec_from_file_location("scanner_web_test", tmp_src)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["scanner_web_test"] = mod
    spec.loader.exec_module(mod)

    app = mod.app
    app.config["TESTING"] = True
    c = app.test_client()

    BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

    def get(path, ua=BROWSER_UA, **kw):
        return c.get(path, headers={"User-Agent": ua}, **kw)

    print("=== 1. baseline + endpoint shape ===")
    j = get("/api/visitors").get_json()
    check("api/visitors returns JSON", isinstance(j, dict), repr(j))
    check("has all_time", "all_time" in j, repr(j))
    check("has baseline", "baseline" in j, repr(j))
    check("has today", "today" in j, repr(j))
    check("baseline starts at 0", j.get("baseline") == 0, repr(j.get("baseline")))

    print("\n=== 2. human page views ARE counted ===")
    before = get("/api/visitors").get_json()["today_hits"]
    get("/")
    get("/pricing")
    get("/pro")
    after = get("/api/visitors").get_json()["today_hits"]
    check("3 human GETs counted", after - before == 3, f"before={before} after={after}")

    print("\n=== 3. bots are NOT counted ===")
    b_hits = get("/api/visitors").get_json()["today_hits"]
    b_uniq = get("/api/visitors").get_json()["today"]
    bots = [
        ("googlebot", "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"),
        ("bingbot", "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"),
        ("indexnow", "IndexNow/1.0"),
        ("curl", "curl/8.4.0"),
        ("wget", "Wget/1.21"),
        ("python-requests", "python-requests/2.31.0"),
        ("uptime monitor", "UptimeRobot/2.0"),
        ("ahrefs", "AhrefsBot/7.0"),
        ("empty UA", ""),
        ("dash UA", "-"),
    ]
    for _, ua in bots:
        get("/", ua=ua)
    a_hits = get("/api/visitors").get_json()["today_hits"]
    a_uniq = get("/api/visitors").get_json()["today"]
    check("no bot counted as a hit", a_hits == b_hits, f"{b_hits} -> {a_hits}")
    check("no bot counted as a unique", a_uniq == b_uniq, f"{b_uniq} -> {a_uniq}")

    print("\n=== 4. IndexNow ping (?url=) is NOT counted ===")
    n_hits = get("/api/visitors").get_json()["today_hits"]
    get("/?url=https://aismarketcap.com/some-page/")
    n_after = get("/api/visitors").get_json()["today_hits"]
    check("IndexNow ping ignored", n_after == n_hits, f"{n_hits} -> {n_after}")

    print("\n=== 5. static/api paths are NOT counted ===")
    s_hits = get("/api/visitors").get_json()["today_hits"]
    for p in ("/health", "/api/pro_pick", "/static/css/x.css", "/robots.txt"):
        get(p)
    s_after = get("/api/visitors").get_json()["today_hits"]
    check("skipped paths ignored", s_after == s_hits, f"{s_hits} -> {s_after}")

    print("\n=== 6. dedup: same IP counted once as unique ===")
    d_uniq = get("/api/visitors").get_json()["today"]
    for _ in range(5):
        get("/")
    d_uniq_after = get("/api/visitors").get_json()["today"]
    check("repeat hits do not inflate unique", d_uniq_after == d_uniq,
          f"{d_uniq} -> {d_uniq_after}")

    print("\n=== 7. different IPs counted as different uniques ===")
    u0 = get("/api/visitors").get_json()["today"]
    c2 = app.test_client()
    c2.get("/", environ_base={"REMOTE_ADDR": "203.0.113.77"},
            headers={"User-Agent": BROWSER_UA})
    u1 = get("/api/visitors").get_json()["today"]
    check("new IP adds a unique", u1 == u0 + 1, f"{u0} -> {u1}")

    print("\n=== 8. POST is not counted ===")
    p_hits = get("/api/visitors").get_json()["today_hits"]
    c.post("/", headers={"User-Agent": BROWSER_UA})
    p_after = get("/api/visitors").get_json()["today_hits"]
    check("POST ignored", p_after == p_hits, f"{p_hits} -> {p_after}")

    print("\n=== 9. redeploy survival: all_time = baseline + live ===")
    mod._flush_visitor_state()
    live_hits = get("/api/visitors").get_json()["since_boot"]
    mod.VISITOR_BASELINE_FILE.write_text(json.dumps({"all_time": 5000}), encoding="utf-8")
    j2 = get("/api/visitors").get_json()
    check("baseline read from git file", j2["baseline"] == 5000, repr(j2["baseline"]))
    check("all_time = baseline + live", j2["all_time"] == 5000 + live_hits,
          f"{j2['all_time']} != 5000 + {live_hits}")

    print("\n=== 10. counter survives a simulated process restart ===")
    mod._flush_visitor_state()
    on_disk = json.loads(mod.VISITOR_FILE.read_text(encoding="utf-8"))
    check("state flushed to disk", on_disk["hits"] == live_hits,
          f"disk={on_disk['hits']} mem={live_hits}")
    check("no raw IP stored anywhere", "203.0.113.77" not in mod.VISITOR_FILE.read_text(encoding="utf-8"))

print("\n" + "=" * 62)
failed = [r for r in results if not r[1]]
print(f"{len(results) - len(failed)}/{len(results)} checks passed")
if failed:
    for n, _, d in failed:
        print(f"  FAILED: {n}  {d}")
    sys.exit(1)
print("ALL CHECKS PASSED")