"""Measure the whole funnel, every link, honestly - including the ones we CANNOT see.

THE CHAIN

    followers -> views -> users -> subscribers -> $5 MRR

This exists because Tyler named that chain as the business, and a funnel you
cannot measure is a funnel you cannot optimize. It runs today and records
history, because a single snapshot every morning looks identical no matter
what changed - the number that matters is the DELTA.

THE BLIND SPOT

`users` (free email signups) is currently unmeasurable. /api/email-list-export
returns 403 because EMAIL_EXPORT_TOKEN is not set on Railway, and the local
email_list.json is written by a pull that has never succeeded. Signups ARE
being captured; nobody can count them. That is reported as UNKNOWN rather than
0, because a zero here would read as "nobody is signing up" when the truth is
"we cannot see anyone signing up". Those are completely different facts and
collapsing them is how a business dies quietly.

Run:  python measure_funnel.py
"""
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = "https://aismarketcap.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")
HISTORY = HERE / "funnel_history.json"
# CMO-owned. Not present yet; the lane writes it. Until then link 1 is UNKNOWN.
FOLLOWERS_FILE = HERE / "bluesky_followers.json"

OPENER = urllib.request.build_opener()
OPENER.addheaders = [("User-Agent", UA)]


def http(path, timeout=25):
    try:
        with OPENER.open(SITE + path, timeout=timeout) as r:
            return r.getcode(), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""


def load_env(path):
    out = {}
    try:
        for line in io.open(path, encoding="utf-8", errors="replace"):
            m = re.match(r"^\s*([A-Z0-9_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                out[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    except Exception:
        pass
    return out


# ---------- each link returns (value, status, source) ------------------------

def link_followers():
    if FOLLOWERS_FILE.exists():
        try:
            d = json.loads(FOLLOWERS_FILE.read_text(encoding="utf-8"))
            n = d.get("followers")
            if isinstance(n, int):
                return n, "OK", "bluesky_followers.json"
        except Exception:
            pass
    return None, "UNKNOWN", "no follower count is recorded on this machine"


def link_views():
    code, body = http("/api/visitors")
    if code != 200:
        return None, "UNKNOWN", "live counter returned HTTP %s" % code
    try:
        d = json.loads(body)
        return d.get("all_time"), "OK", "live /api/visitors all_time=%s today=%s last7=%s" % (
            d.get("all_time"), d.get("today"), d.get("last7"))
    except Exception:
        return None, "UNKNOWN", "counter response was not JSON"


def link_users():
    """Free signups. 403 means we genuinely cannot see them - say so."""
    code, body = http("/api/email-list-export")
    if code == 200:
        try:
            d = json.loads(body)
            items = d if isinstance(d, list) else (d.get("emails") or d.get("list") or [])
            return len(items), "OK", "live export returned %d address(es)" % len(items)
        except Exception:
            return None, "UNKNOWN", "export returned 200 but not parsable JSON"
    local = HERE / "email_list.json"
    if local.exists():
        try:
            d = json.loads(local.read_text(encoding="utf-8"))
            items = d if isinstance(d, list) else list(d.keys())
            return len(items), "OK", "local email_list.json"
        except Exception:
            pass
    return None, "BLIND", ("live export is HTTP %s - no EMAIL_EXPORT_TOKEN on Railway, and "
                           "the local list has never been written. Signups are being "
                           "captured and cannot be counted." % code)


def _stripe_counts():
    """Return (sub_count, unique_customers, mrr).

    sub_count and unique_customers are different numbers and reporting only
    the first one flatters the business. Tyler currently holds TWO active
    subscriptions on ONE email address, so "2 subscribers" is arithmetically
    true and commercially wrong - he is one subscriber who pays twice. The
    goal is the most $5 monthly SUBSCRIBERS, so the unique-customer count is
    the one that belongs in the funnel, with the subscription count kept as
    detail so the discrepancy stays visible instead of being quietly dropped.
    """
    env = load_env(HERE / "stripe_reconcile.env")
    key = env.get("STRIPE_RECONCILE_KEY")
    if not key:
        return None, None, None, "no reconciler key"
    # expand the customer so the EMAIL is available. Counting Stripe customer
    # objects alone is not counting people: Tyler holds two subscriptions
    # under two different customer ids on one email address, so a
    # customer-id count reports 2 subscribers when the business actually has
    # one subscriber who pays twice.
    req = urllib.request.Request(
        "https://api.stripe.com/v1/subscriptions?limit=100&status=all"
        "&expand[]=data.customer",
        headers={"Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        return None, None, None, "stripe read failed: %s" % type(e).__name__
    subs = d.get("data", [])
    active = [s for s in subs if s.get("status") in ("active", "trialing")]
    mrr = 0.0
    for s in active:
        for it in (s.get("items") or {}).get("data", []):
            pr = it.get("price") or {}
            unit = (pr.get("unit_amount") or 0) / 100.0
            qty = it.get("quantity") or 1
            interval = (pr.get("recurring") or {}).get("interval")
            if interval == "year":
                unit = unit / 12.0
            mrr += unit * qty
    people, no_email = set(), 0
    for s in active:
        c = s.get("customer")
        email = c.get("email") if isinstance(c, dict) else None
        if email:
            people.add(str(email).strip().lower())
        else:
            # An unidentifiable subscriber must not be counted as unique on
            # hope, and must not silently merge either. Mark it distinctly.
            no_email += 1
            people.add("unidentified:" + str(s.get("id")))
    if no_email:
        print("WARN %d active subscription(s) had no expanded email; they are "
              "counted as distinct unidentified people." % no_email)
    return len(active), len(people), round(mrr, 2), "stripe live"


def link_subscribers():
    subs, people, _, _ = _stripe_counts()
    if people is None:
        return None, "UNKNOWN", "stripe unavailable"
    src = "stripe live - %d subscription(s) across %d unique customer(s)" % (subs, people)
    return people, "OK", src


def link_mrr():
    subs, people, mrr, _ = _stripe_counts()
    if mrr is None:
        return None, "UNKNOWN", "stripe unavailable"
    return mrr, "OK", "stripe live across %d unique customer(s)" % (people or 0)


LINKS = [
    ("followers", "Bluesky audience", link_followers),
    ("views", "site page views", link_views),
    ("users", "free email signups", link_users),
    ("subscribers", "paying customers", link_subscribers),
    ("mrr", "monthly revenue", link_mrr),
]


def load_history():
    if HISTORY.exists():
        try:
            return json.loads(HISTORY.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def main():
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    snapshot, printable = {}, []

    for key, label, fn in LINKS:
        val, status, src = fn()
        snapshot[key] = {"value": val, "status": status, "source": src, "at": now}
        printable.append((key, label, val, status, src))

    history = load_history()
    history.append(snapshot)
    # 90 days is plenty for a daily meeting and keeps the file small.
    if len(history) > 90:
        history = history[-90:]
    try:
        HISTORY.write_text(json.dumps(history, indent=2), encoding="utf-8")
    except Exception as e:
        print("WARN could not record history: %s" % e)

    prev = history[-2] if len(history) >= 2 else None

    print("=" * 78)
    print("FUNNEL  %s" % now)
    print("=" * 78)
    print("%-13s %-22s %12s   %s" % ("link", "what", "value", "delta"))
    print("-" * 78)
    for key, label, val, status, src in printable:
        shown = "UNKNOWN" if val is None else (f"{val:,}" if isinstance(val, int) else f"{val}")
        delta = ""
        if prev and prev.get(key, {}).get("value") is not None and val is not None:
            d = val - prev[key]["value"]
            if d:
                delta = "%+d since last run" % d
            else:
                delta = "no change"
        elif val is None:
            delta = "*** CANNOT BE MEASURED ***"
        print("%-13s %-22s %12s   %s" % (key, label, shown, delta))
        if status != "OK":
            print("             ! %s" % src)
    print("-" * 78)

    blind = [k for k, _, v, s, _ in printable if v is None]
    if blind:
        print()
        print("BLIND LINKS: %s" % ", ".join(blind))
        print("A daily meeting that optimizes a funnel it cannot see is guessing.")
        print("Every other number is a fact; these are not, and must not be")
        print("reported as zero - zero means 'measured and nobody', which is a")
        print("completely different claim from 'not instrumented'.")

    print()
    print("THE ONE QUESTION: of the links we CAN see, which is the constraint?")
    print("Everything upstream of it is worth nothing until it moves.")
    print("history: %s" % HISTORY.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())