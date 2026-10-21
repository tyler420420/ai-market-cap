"""
DAILY CONTENT PIPELINE — trending-driven article briefs + queue gate.

Runs at 7 AM before the 8 AM publisher. Two jobs:

  1. BRIEF   Scan what people are actually searching about today and write
             article briefs (target ticker, angle, keyword) for the top N
             opportunities. This is what the writer consumes.

  2. GATE    Any article sitting in article_queue/ is scored before it is
             allowed to publish. Template filler is rejected, not shipped.

The pipeline never writes article prose itself — there is no LLM API key
configured on this host, so prose is written by the agent (traffic_writer)
and validated here. That split is deliberate: data in, quality control, and
the writing both stay in one place.

Usage:
    python daily_content_pipeline.py brief   # generate today's briefs
    python daily_content_pipeline.py gate    # score queued articles
    python daily_content_pipeline.py run     # both
"""

import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from trending_scanner import scan  # noqa: E402
import quality_gate as qg  # noqa: E402

BASE = Path(__file__).parent
QUEUE = BASE / "article_queue"
BRIEFS = BASE / "content_briefs.json"

TARGET_PER_DAY = 10  # ceiling; the gate decides how many actually ship

# Angle templates keyed to search intent. These produce real questions people
# type, never the spun "why does X" nonsense from the old keyword rotator.
ANGLES = [
    ("ticker_earnings", "{sym} earnings date {month} {year}",
     "When does {sym} report, what the street expects, and how to trade the pre-earnings window"),
    ("ticker_setup", "{sym} pre-earnings setup",
     "Score, price action and analyst positioning on {sym} into its print"),
    ("sector_roundup", "AI stocks earnings {month} {year}",
     "The AI names reporting this month and which have the cleanest pre-earnings setups"),
    ("ticker_move", "why is {sym} stock moving today",
     "What is driving {sym} today and whether the move is tradeable"),
    ("ticker_vs", "{sym} vs peers AI infrastructure",
     "Where {sym} sits against comparable AI infrastructure names on valuation and growth"),
]


def _month_year():
    now = datetime.now()
    return now.strftime("%B"), now.strftime("%Y")


def published_titles():
    idx = Path(r"C:\Users\Tyler_AI\ai-market-cap\blog\index.json")
    try:
        return [a.get("title", "") for a in json.loads(idx.read_text(encoding="utf-8"))]
    except Exception:
        return []


def build_briefs(top_n=TARGET_PER_DAY):
    trending = scan(top_n=top_n)
    month, year = _month_year()
    live = published_titles()
    briefs = []

    for t in trending:
        sym = t["symbol"]
        name = t.get("name") or sym
        angle_key, kw_tpl, angle = ANGLES[len(briefs) % len(ANGLES)]
        keyword = kw_tpl.format(sym=sym, month=month, year=year)

        # Don't brief something already covered.
        if any(sym.lower() in (p or "").lower() for p in live):
            continue

        briefs.append({
            "symbol": sym,
            "name": name,
            "angle_type": angle_key,
            "angle": angle.format(sym=sym),
            "target_keyword": keyword,
            "score": t.get("score"),
            "yahoo_rank": t.get("yahoo_rank"),
            "pct_change": t.get("pct_change"),
            "price": t.get("price"),
            "why_now": (
                f"{sym} is #{t.get('yahoo_rank')} on Yahoo Finance trending today"
                + (f", moving {t['pct_change']:+.1f}%" if t.get("pct_change") is not None else "")
            ),
        })

    payload = {
        "generated_at": datetime.now().isoformat(),
        "date": date.today().isoformat(),
        "target": TARGET_PER_DAY,
        "count": len(briefs),
        "briefs": briefs,
    }
    BRIEFS.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return briefs


def gate_queue():
    """Score every queued article; move rejects out so they never publish."""
    if not QUEUE.exists():
        print("  (no queue dir)")
        return 0, 0
    live = published_titles()
    approved, rejected = 0, 0
    reject_dir = QUEUE / "rejected"

    for qf in sorted(QUEUE.glob("aismarketcap_*.json")):
        try:
            art = json.loads(qf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [SKIP] {qf.name}: unreadable ({e})")
            continue

        typ = "wins" if "wins" in (art.get("keyword", "") or "").lower() or \
                       "this week's top" in (art.get("title", "") or "").lower() else "standard"
        v = qg.evaluate(art, live, article_type=typ)

        if v["pass"]:
            approved += 1
            print(f"  [PASS {v['score']:>3}] {art.get('title','')[:56]}")
            for w in v.get("warnings", []):
                print(f"          warn: {w}")
        else:
            rejected += 1
            print(f"  [REJECT {v['score']:>3}] {art.get('title','')[:56]}")
            for r in v["reasons"][:3]:
                print(f"          - {r}")
            reject_dir.mkdir(exist_ok=True)
            qf.replace(reject_dir / qf.name)

    return approved, rejected


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    print("=" * 62)
    print(f"  DAILY CONTENT PIPELINE — {datetime.now():%Y-%m-%d %H:%M}")
    print("=" * 62)

    if mode in ("brief", "run"):
        briefs = build_briefs()
        print(f"\n  BUILT {len(briefs)} CONTENT BRIEFS:\n")
        for b in briefs:
            print(f"   [{b['symbol']:<6}] {b['target_keyword']}")
            print(f"            {b['why_now']}")

    if mode in ("gate", "run"):
        print("\n  GATING QUEUED ARTICLES:")
        approved, rejected = gate_queue()
        print(f"\n  approved={approved}  rejected={rejected}")


if __name__ == "__main__":
    main()