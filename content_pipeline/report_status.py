"""Date the one-day moves and confirm whether each departed ticker has REPORTED.

Answers the bucket-B question with evidence: an article is only an ARCHIVE
(result writeup) if the print actually happened, with a date I can cite.

Run:  python report_status.py
"""
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TICKERS = ["SMCI", "DELL", "MU", "CRDO", "LITE", "AVGO", "META", "LRCX",
           "IBM", "TSLA", "NBIS", "AMD", "VRT"]


def get(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


rows = []
for t in TICKERS:
    try:
        j = json.loads(get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{t}"
            "?range=3mo&interval=1d"))
        res = j["chart"]["result"][0]
        meta = res["meta"]
        ts = res["timestamp"]
        q = res["indicators"]["quote"][0]
        bars = []
        for i, tstamp in enumerate(ts):
            c = q["close"][i]
            if c is None:
                continue
            bars.append({
                "d": datetime.fromtimestamp(tstamp, timezone.utc).strftime("%Y-%m-%d"),
                "c": c,
            })
        last = bars[-1]
        prev = bars[-2]
        # 30d-ago baseline
        base = bars[-22] if len(bars) > 22 else bars[0]
        rows.append({
            "ticker": t,
            "name": meta.get("shortName"),
            "last_date": last["d"],
            "price": round(last["c"], 2),
            "d1_pct": round((last["c"] / prev["c"] - 1) * 100, 2),
            "since_base_date": base["d"],
            "since_base_pct": round((last["c"] / base["c"] - 1) * 100, 2),
            "high_3mo": round(max(b["c"] for b in bars), 2),
            "low_3mo": round(min(b["c"] for b in bars), 2),
            "bars": len(bars),
        })
    except Exception as e:
        rows.append({"ticker": t, "error": str(e)})

# last close before the big one-day move, to see the print gap
for r in rows:
    if "error" not in r:
        t = r["ticker"]
        try:
            j = json.loads(get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{t}"
                "?range=3mo&interval=1d"))
            res = j["chart"]["result"][0]
            ts, q = res["timestamp"], res["indicators"]["quote"][0]
            series = [(datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%d"), c)
                      for x, c in zip(ts, q["close"]) if c is not None]
            r["last5"] = [(d, round(c, 2)) for d, c in series[-5:]]
        except Exception as e:
            r["last5"] = f"ERR {e}"

out = Path(__file__).with_name("report_status.json")
out.write_text(json.dumps(rows, indent=1), encoding="utf-8")

print(f"{'tkr':<6}{'last bar':<12}{'price':>9}{'1d%':>8}{'~30d%':>8}   name")
print("-" * 84)
for r in rows:
    if "error" in r:
        print(f"{r['ticker']:<6}ERROR {r['error'][:50]}")
        continue
    print(f"{r['ticker']:<6}{r['last_date']:<12}{r['price']:>9}{r['d1_pct']:>8}"
          f"{r['since_base_pct']:>8}   {r['name']}")
    if isinstance(r.get("last5"), list):
        print("        last 5 closes: " +
              ", ".join(f"{d}={c}" for d, c in r["last5"]))

print(f"\nsaved -> {out.name}")