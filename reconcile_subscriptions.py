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


def discover(stripe_mod, subs):
    """Find paying customers Stripe knows about and we have no local record of.

    Returns (additions, error). `additions` maps customer id -> new record.
    On any failure it returns an empty dict: discovery can only ever ADD
    evidence that someone is paying, so every failure mode is "add nothing".

    THE BLIND SPOT THIS CLOSES
    -------------------------
    This script used to read subscriptions.json as its INPUT and ask Stripe
    about each key it already held. That is a one-way sync. It can re-verify
    customers it knows about; it can never notice a new one.

    Two things make that blindness load-bearing:
      * /webhook fails closed while STRIPE_WEBHOOK_SECRET is unset (correctly -
        an unsigned body must never be able to revoke a paying customer), so no
        lifecycle event ever arrives.
      * The only other local write is /success, and subscriptions.json lives on
        Railway's EPHEMERAL container disk. A redeploy erases it.

    So the first genuinely new subscriber gets written somewhere that does not
    survive, never enters this file, and send_daily_alert.py - which reads
    exactly this file - never emails them the Pro alert they paid for.

    And nothing reports it. is_subscriber() falls back to live Stripe, so the
    customer can log in and see Pro working perfectly while the paid daily email
    they are paying for silently never arrives. Both ends look healthy.

    Verified on 2026-10-22: Stripe held 2 active subscriptions, this file held
    1. Same person on both, so nothing was actually lost yet - which is exactly
    why it would have gone unnoticed until a real customer arrived.

    SAFETY - unchanged, and deliberately one-directional:
      * Only ADDS records Stripe positively reports as "active".
      * Never downgrades, never upgrades, never edits an existing record.
      * A discovery error adds nothing and never reaches the downgrade path.
    """
    try:
        r = stripe_mod.Subscription.list(status="active", limit=100,
                                         expand=["data.customer"])
        items = getattr(r, "data", None) or []
    except Exception as e:
        # Includes a stub/module that does not accept expand=. Nothing is added
        # and the downgrade loop still runs exactly as before.
        return {}, "%s: %s" % (type(e).__name__, e)

    found = {}
    for s in items:
        if getattr(s, "status", None) != "active":
            continue
        cust = getattr(s, "customer", None)
        if isinstance(cust, str):
            cid, email = cust, None
        elif isinstance(cust, dict):
            cid, email = cust.get("id"), cust.get("email")
        else:
            cid = getattr(cust, "id", None)
            email = getattr(cust, "email", None)
        if not cid or cid in subs:
            continue
        rec = {"status": "active",
               "source": "discovered_from_stripe",
               "discovered_at": datetime.now().isoformat(timespec="seconds")}
        if email:
            rec["email"] = email
        found[cid] = rec
    return found, None


def reconcile(dry=False):
    subs = load_subs()
    if subs is None:
        return 1

    actives = [(cid, rec) for cid, rec in subs.items()
               if isinstance(rec, dict) and rec.get("status") == "active"]
    print(f"[Reconcile] {len(actives)} active subscription(s) to check")

    # Discovery runs BEFORE the "nothing to check" exit, because having no local
    # records at all is precisely the state where a new subscriber is invisible.
    key = load_key()
    discovered, disc_err = {}, None
    if key:
        import stripe as stripe_mod
        stripe_mod.api_key = key
        discovered, disc_err = discover(stripe_mod, subs)
        for cid, rec in discovered.items():
            print(f"[Reconcile] DISCOVERED {cid} active in Stripe with no local "
                  f"record -> adding (email={'yes' if rec.get('email') else 'unknown'})")
        if disc_err:
            print(f"[Reconcile] discovery skipped, nothing added ({disc_err})")
    else:
        # NOT CONFIGURED is a normal, honest state - never a crash, and it
        # must not touch a single record.
        print("[Reconcile] NOT CONFIGURED - put a READ-ONLY restricted key in "
              "stripe_reconcile.env. No records were changed.")

    if not actives:
        if discovered and not dry:
            subs.update(discovered)
            save_subs(subs)
        write_status({"last_run": datetime.now().isoformat(timespec="seconds"),
                      "checked": 0, "downgraded": 0, "unknown": 0,
                      "discovered": len(discovered), "last_ok": True,
                      "configured": bool(key)})
        return 0

    if not key:
        write_status({"last_run": datetime.now().isoformat(timespec="seconds"),
                      "checked": 0, "downgraded": 0, "unknown": 0,
                      "discovered": 0, "last_ok": True, "configured": False})
        return 0

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

    if (downgraded or discovered) and not dry:
        subs.update(discovered)
        save_subs(subs)

    # last_ok means "the reconcile itself worked", not "every record was
    # verifiable". One permanently unverifiable record - a test fixture with a
    # fake customer id, say - would otherwise pin this false forever and make a
    # real outage indistinguishable from normal noise. It goes false only when
    # NOTHING could be checked, which is what an actual API failure looks like.
    resolved = len(actives) - len(unknown)
    write_status({
        "last_run": datetime.now().isoformat(timespec="seconds"),
        "checked": len(actives),
        "resolved": resolved,
        "downgraded": len(downgraded),
        "unknown": len(unknown),
        "unknown_ids": unknown,
        "discovered": len(discovered),
        "last_ok": bool(resolved > 0 or not actives),
        "configured": True,
        "dry_run": bool(dry),
    })
    print(f"[Reconcile] checked={len(actives)} resolved={resolved} "
          f"downgraded={len(downgraded)} unknown={len(unknown)}"
          f" discovered={len(discovered)}"
          f"{' (DRY RUN)' if dry else ''}")
    if unknown:
        # Not a crash: some customers could not be verified this run.
        print("[Reconcile] some customers were unverifiable and were left "
              "untouched, which is the safe direction")
    return 0


if __name__ == "__main__":
    sys.exit(reconcile(dry="--dry-run" in sys.argv))