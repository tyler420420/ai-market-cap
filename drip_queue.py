#!/usr/bin/env python3
"""Build the drip queue: free signups, minus anyone already paying.

WHY THIS FILE EXISTS AND WHY IT IS THE ONLY ONE THAT READS BOTH LISTS
The drip must reach people who signed up for the free pick AND must not reach
someone who already pays - email 4 is "what Pro adds", which is nonsense to
send a paying customer, and email 6 retires them from a sequence they never
joined.

That needs both populations. So the join happens HERE, once, and the result is
written to drip_queue.json. drip_send.py opens only that file. The mistake is
then an ImportError rather than a wrong recipient.

Also applied here:
  * unsubscribed addresses never enter the queue
  * addresses in email_do_not_send.txt are dropped, and that file is VALIDATED
    on load - the first version of it was "address<TAB>domain" on all ten
    lines, so it matched nothing while looking maintained. A suppression list
    that suppresses nothing is the worst artifact there is.

Run:  python drip_queue.py [--dry-run]
Exit 0 = queue written. Exit 1 = nothing safe to write.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

SITE = Path(__file__).parent
FREE_LIST = SITE / "email_list.json"
SUBS = SITE / "subscriptions.json"
DO_NOT_SEND = SITE / "email_do_not_send.txt"
QUEUE = SITE / "drip_queue.json"
DONE = SITE / "drip_retired.json"
PT_TZ = None
try:
    from zoneinfo import ZoneInfo
    PT_TZ = ZoneInfo("America/Los_Angeles")
except Exception:
    pass


def load(name, default):
    try:
        return json.loads((SITE / name).read_text(encoding="utf-8"))
    except Exception:
        return default


def load_suppression():
    """Read the do-not-send file, and REFUSE it if it is not a plain address list.

    Ten lines of 'address<TAB>domain' once sat in that file. Every structural
    check passed because there is no structural check, and it suppressed zero
    addresses. So the format is asserted here rather than trusted: if any
    non-comment line is not a bare address, the file is treated as broken and
    the caller is told, instead of quietly matching nothing.
    """
    if not DO_NOT_SEND.exists():
        return set(), None
    good, bad = set(), 0
    for line in DO_NOT_SEND.read_text(encoding="utf-8",
                                      errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.count("@") == 1 and "\t" not in s and " " not in s:
            good.add(s.lower())
        else:
            bad += 1
    note = None
    if bad:
        note = ("%s has %d line(s) that are not bare addresses; they will be "
                "ignored. A suppression file must be one address per line with "
                "no trailing text." % (DO_NOT_SEND.name, bad))
    return good, note


def main():
    dry = "--dry-run" in sys.argv
    free = load("email_list.json", {})
    subs = load("subscriptions.json", {})
    retired = load("drip_retired.json", {})
    suppress, note = load_suppression()
    if note:
        print("[Queue] WARNING - " + note)

    if not isinstance(free, dict) or not free:
        print("[Queue] no free signups pulled yet - nothing to do")
        return 0

    # Anyone with an ACTIVE subscription has already converted. They get the
    # daily pick with the real values; a drip would add nothing and email 4
    # would tell a paying customer what they already bought.
    paying = set()
    for _cid, rec in (subs.items() if isinstance(subs, dict) else []):
        if isinstance(rec, dict) and rec.get("status") == "active":
            e = (rec.get("email") or "").strip().lower()
            if e:
                paying.add(e)

    today = datetime.now(PT_TZ).strftime("%Y-%m-%d") if PT_TZ \
        else datetime.now().strftime("%Y-%m-%d")
    rows, dropped_unsubscribed, dropped_paying, dropped_suppressed = [], 0, 0, 0
    for email, rec in free.items():
        e = (email or "").strip().lower()
        if not e:
            continue
        if isinstance(rec, dict) and rec.get("unsubscribed"):
            dropped_unsubscribed += 1
            continue
        if e in suppress:
            dropped_suppressed += 1
            continue
        if e in paying:
            dropped_paying += 1
            continue
        rows.append({
            "email": e,
            "added": (rec or {}).get("added") or "",
            # When the person signed up is when email #1 is due. Falling back
            # to today keeps a malformed date from silently parking someone
            # in the queue forever.
            "day0": (rec or {}).get("added") or today,
        })

    rows.sort(key=lambda r: r["email"])
    print("[Queue] free signups      : %d" % len(free))
    print("[Queue] dropped unsubscribed: %d" % dropped_unsubscribed)
    print("[Queue] dropped on do-not-send: %d" % dropped_suppressed)
    print("[Queue] dropped because paying: %d" % dropped_paying)
    print("[Queue] queued for the drip : %d" % len(rows))

    if dry:
        print("[Queue] DRY RUN - not written")
        return 0
    if not rows:
        print("[Queue] nothing to write")
        return 0

    try:
        QUEUE.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    except Exception as e:
        print("[Queue] could not write the queue: %s" % e)
        return 1
    print("[Queue] written to %s (gitignored - it holds addresses)" % QUEUE.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())