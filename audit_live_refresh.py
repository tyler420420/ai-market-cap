"""Is the live site serving the Refresh button, and did the FAQ stop
promising on-demand scans?

Gates on /api/visitors returning 200 first. Read-only.
"""
import re
import sys
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
BASE = "https://aismarketcap.com"
failures = []


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL") + f"  {name}" + ("" if ok else f"  -- {detail}"))
    if not ok:
        failures.append(name)


def get(path):
    return urllib.request.urlopen(
        urllib.request.Request(BASE + path, headers={"User-Agent": UA}),
        timeout=40).read().decode("utf-8", "replace")


def main():
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(BASE + "/api/visitors",
                                   headers={"User-Agent": UA}), timeout=25)
        check("/api/visitors 200 (deploy gate)", r.status == 200, f"got {r.status}")
    except urllib.error.HTTPError as e:
        check("/api/visitors 200 (deploy gate)", False, f"HTTP {e.code}")
        return 1

    home = get("/")
    check("live home page has the Refresh button", ">Refresh</button>" in home)
    check("live home page has no Scan button", ">Scan</button>" not in home)
    check("live page cannot start a scan", "/run" not in home,
          "the deployed page still references /run")
    check("runScan() is gone from the live page", "function runScan(" not in home)
    check("refreshData() is present", "function refreshData()" in home)
    check("no false 'scan queued' claim in the live page",
          "queued_locally" not in home and "already_pending" not in home)

    about = get("/about")
    check("live FAQ no longer promises additional scans",
          "additional scans" not in about.lower(),
          "the FAQ is still selling scans that do not run")
    check("live FAQ describes the automatic daily scan",
          "runs automatically every market day" in about)
    check("live FAQ points at the Refresh button", "Refresh" in about)

    pricing = get("/pricing")
    check("pricing page never promised scans (nothing sold was withdrawn)",
          "additional scan" not in pricing.lower())

    print(f"\n=== {'ALL PASS' if not failures else str(len(failures)) + ' FAILURE(S)'} ===")
    for f in failures:
        print(f"   - {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())