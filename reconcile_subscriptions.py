#!/usr/bin/env python3
"""Reconcile local subscription status against Stripe, once a day.

THE GAP THIS CLOSES
-------------------
STRIPE_WEBHOOK_SECRET is not set, and /webhook deliberately fails closed when
it is missing - the right call, because an unsigned body must never be able to
revoke a paying customer.

But that means the ONLY way a cancellation or a failed renewal reaches the
site is... nothing. It does not reach it at all.

And is_subscriber() cannot catch it either:

    local_status = local.get('status')
    if local_status == 'active':
        return True          # short-circuits before Stripe is ever asked
    ... ask Stripe ...

The live Stripe re-validation exists to rescue a wrongly-DENIED customer. It
never runs for a wrongly-GRANTED one. So a customer who cancels in Stripe
keeps access here indefinitely, and nothing in the system notices.

This is the webhook's job done the slow, boring way.

TWO SAFETY RULES, AND THEY ARE NOT SYMMETRIC
-------------------------------------------
1. Downgrade ONLY on a positive "this subscription is not active" from Stripe.
   A network error, a timeout, a missing key, an unparseable response, an
   empty customer id - every one of those leaves access untouched. The failure
   mode must be "we failed to notice a cancellation", never "we denied a
   paying customer". Being wrong in that direction costs real money and real
   trust; being wrong in the other direction costs one missed cancellation.

2. Never upgrade and never touch anything Stripe still calls active. A
   downgrade can only ever be active -> cancelled / past_due.

Run:  python reconcile_subscriptions.py [--dry-run]
Exit 0 = reconciled (including "nothing to do" and "not configured").
Exit 1 = something went wrong that a human should look at.
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
KEY_FILE = HERE / "stripe_reconcile.env"
STATUS_FILE = HERE / "reconcile_status.json"

# Stripe subscription statuses that mean "not paying any more".
DEAD = ("canceled", "incomplete_expired", "unpaid")
# Statuses we may write locally when Stripe says one of these.
DOWNGRADE_TO = {
    "canceled": "cancelled",
    "incomplete_expired": "past_due",
    "unpaid": "past_due",
}


def load_key():
    """Read the reconcile key from the file, then the environment."""
    key = ""
    if KEY_FILE.exists():
        for line in KEY_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == "STRIPE_RECONCILE_KEY":
                key = v.strip().strip('"').strip("'")
    return key or (os.environ.get("STRIPE_RECONCILE_KEY") or "").strip()


def load_subs():
    p = HERE / "subscriptions.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[Reconcile] cannot read subscriptions.json: {e}")
        return None
    return data if isinstance(data, dict) else None


def save_subs(data):
    (HERE / "subscriptions.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8")


def write_status(payload):
    try:
        STATUS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[Reconcile] could not write status: {e}")


def real_status(stripe_mod, customer_id):
    """Return (status_string, error). status is None when we do not know.

    None means UNKNOWN and callers must leave the record alone. Only a real
    status string from Stripe counts as an answer.
    """
    try:
        r = stripe_mod.Subscription.list(customer=customer_id, limit=1, status="all")
        items = getattr(r, "data", None) or []
        if not items:
            # No subscription at all is a positive answer only if Stripe
            # answered cleanly - which it did, since we got here without an
            # exception. An empty list is not an error.
            return "canceled", None
        sub = items[0]
        status = getattr(sub, "status", None)
        if not status:
            return None, "subscription returned without a status"
        return status, None
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)


def reconcile(dry=False):
    subs = load_subs()
    if subs is None:
        return 1

    actives = [(cid, rec) for cid, rec in subs.items()
               if isinstance(rec, dict) and rec.get("status") == "active"]
    print(f"[Reconcile] {len(actives)} active subscription(s) to check")
    if not actives:
        write_status({"last_run": datetime.now().isoformat(timespec="seconds"),
                      "checked": 0, "downgraded": 0, "unknown": 0, "last_ok": True})
        return 0

    key = load_key()
    if not key:
        # NOT CONFIGURED is a normal, honest state - never a crash, and it
        # must not touch a single record.
        print("[Reconcile] NOT CONFIGURED - put a READ-ONLY restricted key in "
              "stripe_reconcile.env. No records were changed.")
        write_status({"last_run": datetime.now().isoformat(timespec="seconds"),
                      "checked": 0, "downgraded": 0, "unknown": 0,
                      "last_ok": True, "configured": False})
        return 0

    import stripe as stripe_mod
    stripe_mod.api_key = key

    downgraded, unknown, ok = [], [], True
    for cid, rec in actives:
        status, err = real_status(stripe_mod, cid)
        if status is None:
            # UNKNOWN -> touch nothing. This is the whole safety story.
            unknown.append(cid)
            print(f"[Reconcile] UNKNOWN {cid} -> leaving access untouched ({err})")
            continue
        if status in DEAD:
            new = DOWNGRADE_TO.get(status, "cancelled")
            downgraded.append(cid)
            print(f"[Reconcile] DOWNGRADE {cid}: local=active stripe={status} -> {new}")
            if not dry:
                rec["status"] = new
                rec["reconciled_at"] = datetime.now().isoformat(timespec="seconds")
                rec["reconciled_reason"] = "stripe says %s" % status
        else:
            ok = True
            print(f"[Reconcile] ok {cid}: stripe={status}")

    if downgraded and not dry:
        save_subs(subs)

    write_status({
        "last_run": datetime.now().isoformat(timespec="seconds"),
        "checked": len(actives),
        "downgraded": len(downgraded),
        "unknown": len(unknown),
        "last_ok": len(unknown) == 0,
        "configured": True,
        "dry_run": bool(dry),
    })
    print(f"[Reconcile] checked={len(actives)} downgraded={len(downgraded)} "
          f"unknown={len(unknown)}{' (DRY RUN)' if dry else ''}")
    if unknown:
        # Not a crash: some customers could not be verified this run.
        print("[Reconcile] some customers were unverifiable and were left "
              "untouched, which is the safe direction")
    return 0


if __name__ == "__main__":
    sys.exit(reconcile(dry="--dry-run" in sys.argv))