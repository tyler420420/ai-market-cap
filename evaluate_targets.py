#!/usr/bin/env python3
"""Track picks over time and detect when one actually reaches its target.

WHY THIS EXISTS
---------------
The original growth note said: "annual nudge when a pick hits its target -
that's the exact moment someone buys." That was not buildable, because
pick_tracker.json is OVERWRITTEN on every scan. It holds only the five picks
made by the most recent run, so the previous day's picks - and every day's
after that - are gone. A file called "pick_tracker" that tracks nothing.

So this adds the history the nudge needs, without touching the generator:

  tracked_picks.jsonl   append-only, one JSON object per tracked pick
  target_hits.json      regenerated each run: picks that REACHED their target

Honesty rules, because this feeds a sales pitch:

  * A hit counts only when the live price is >= the target recorded on the day
    the pick was made. Nothing is inferred, rounded up, or "close enough".
  * Every number rendered comes from a real fetch. A ticker whose price could
    not be fetched is recorded as `unchecked`, never counted as a hit and never
    quietly dropped.
  * If there are no hits, the file says so with an empty list. The pricing page
    renders nothing at all in that case - no placeholder urgency, no fake
    countdown.

Run:  python evaluate_targets.py
Exit 0 = evaluated (even with zero hits). Exit 1 = could not evaluate.
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).parent
TRACKER = HERE / "pick_tracker.json"
HISTORY = HERE / "tracked_picks.jsonl"
OUT = HERE / "target_hits.json"

# A pick older than this has told us what it had to tell. Earnings plays are
# meant to resolve within weeks.
WINDOW_DAYS = 90
# A hit stops being "the moment" after this long - the nudge is a nudge, not
# an archive.
FRESH_DAYS = 14


def load_today():
    try:
        data = json.loads(TRACKER.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[Targets] cannot read pick_tracker.json: {e}")
        return []
    return data if isinstance(data, list) else []


def load_history():
    rows = []
    if HISTORY.exists():
        for line in HISTORY.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                # A truncated last line from an interrupted run must not stop
                # the history from loading.
                continue
    return rows


def append_history(today):
    """Append today's picks, skipping any (date, ticker) already recorded."""
    have = {(r.get("date"), r.get("ticker")) for r in load_history()}
    added = 0
    with open(HISTORY, "a", encoding="utf-8") as f:
        for p in today:
            key = (p.get("date"), p.get("ticker"))
            if key in have:
                continue
            if not p.get("ticker") or not p.get("pe_target"):
                continue
            f.write(json.dumps({
                "date": p.get("date"),
                "ticker": p.get("ticker"),
                "company": p.get("company", ""),
                "entry": p.get("price"),
                "score": p.get("score"),
                "target": p.get("pe_target"),
            }) + "\n")
            have.add(key)
            added += 1
    return added


def price_now(ticker):
    import yfinance as yf
    h = yf.Ticker(ticker).history(period="1d")
    if h is None or not len(h):
        return None
    return float(h["Close"].iloc[-1])


def evaluate():
    today = load_today()
    if not today:
        print("[Targets] pick_tracker.json is empty - nothing to evaluate")
        return None
    added = append_history(today)
    history = load_history()
    print(f"[Targets] history: {len(history)} tracked pick(s) (+{added} new)")

    cutoff = (datetime.now() - timedelta(days=WINDOW_DAYS)).strftime("%Y-%m-%d")
    in_window = [r for r in history if (r.get("date") or "") >= cutoff]
    print(f"[Targets] {len(in_window)} within the {WINDOW_DAYS}-day window")

    hits, checked, unchecked = [], 0, 0
    for r in in_window:
        px = None
        try:
            px = price_now(r["ticker"])
        except Exception as e:
            print(f"[Targets] {r['ticker']}: price fetch failed ({type(e).__name__})")
        if px is None or not r.get("target"):
            # Not a hit and not a miss. Saying nothing is the only honest
            # option; counting it either way would invent evidence.
            unchecked += 1
            continue
        checked += 1
        tgt = float(r["target"])
        if px >= tgt:
            gain = round((px / tgt - 1) * 100, 1)
            hits.append({
                "date": r.get("date"),
                "ticker": r.get("ticker"),
                "company": r.get("company", ""),
                "entry": r.get("entry"),
                "target": round(tgt, 2),
                "current": round(px, 2),
                "vs_target_pct": gain,
                "days_to_hit": (datetime.now().date() -
                                datetime.strptime(r["date"], "%Y-%m-%d").date()).days,
            })

    payload = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "window_days": WINDOW_DAYS,
        "fresh_days": FRESH_DAYS,
        "tracked_total": len(history),
        "tracked_in_window": len(in_window),
        "checked": checked,
        "unchecked": unchecked,
        "hit_count": len(hits),
        "hits": sorted(hits, key=lambda h: h.get("date") or "", reverse=True),
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[Targets] checked={checked} unchecked={unchecked} HITS={len(hits)} -> {OUT.name}")
    for h in payload["hits"]:
        print(f"[Targets]   {h['ticker']} target ${h['target']} met at ${h['current']} "
              f"(flagged {h['date']})")
    return payload


if __name__ == "__main__":
    r = evaluate()
    sys.exit(0 if r is not None else 1)