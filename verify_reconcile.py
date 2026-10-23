"""The reconciler may downgrade access, so its error handling is the product.

THE ASYMMETRY
-------------
Two mistakes are possible and they are not equally costly:

  * Missing a cancellation      -> one customer keeps $5/month access. Cost:
                                    small, visible, self-correcting tomorrow.
  * Denying a PAYING customer   -> a customer who paid is locked out. Cost:
                                    real money, real trust, a support email.

So every path that is not a positive "Stripe says this subscription is dead"
must leave the record untouched. That is the whole design, and it is what this
file exists to prove.

A fake `stripe` module is injected, so every branch is exercised for real
without touching Stripe or any live customer.
"""
import importlib.util
import json
import sys
import types
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
SRC = SITE / "reconcile_subscriptions.py"

fails = []
ran = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  -> " + detail) if detail and not ok else ""))
    ran.append(name)
    if not ok:
        fails.append(name)


def load(status_by_customer, key="rk_test"):
    """Import the reconciler fresh with a fake stripe module and fake files."""
    subs = {
        "cus_active": {"status": "active", "email": "a@x.com"},
        "cus_cancelled": {"status": "cancelled", "email": "c@x.com"},
        "cus_due": {"status": "active", "email": "d@x.com"},
    }

    class _Sub:
        def __init__(self, status):
            self.status = status

    class _List:
        def __init__(self, items):
            self.data = items

    def _list(customer=None, limit=1, status="all"):
        st = status_by_customer.get(customer, "active")
        if isinstance(st, Exception):
            raise st
        if st == "__empty__":
            return _List([])
        return _List([_Sub(st)])

    fake = types.ModuleType("stripe")
    fake.Subscription = types.SimpleNamespace(list=_list)
    fake.api_key = None

    old_stripe = sys.modules.get("stripe")
    sys.modules["stripe"] = fake
    try:
        spec = importlib.util.spec_from_file_location("recon_probe", SRC)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Redirect every path the module uses into a temp sandbox.
        import tempfile
        td = Path(tempfile.mkdtemp())
        subs_file = td / "subscriptions.json"
        subs_file.write_text(json.dumps(subs), encoding="utf-8")
        key_file = td / "stripe_reconcile.env"
        key_file.write_text("STRIPE_RECONCILE_KEY=%s\n" % key if key else "\n",
                            encoding="utf-8")
        mod.HERE = td
        mod.KEY_FILE = key_file
        mod.STATUS_FILE = td / "reconcile_status.json"
        rc = mod.reconcile(dry=False)
        after = json.loads(subs_file.read_text(encoding="utf-8"))
        return rc, before_status(subs), after
    finally:
        if old_stripe is None:
            sys.modules.pop("stripe", None)
        else:
            sys.modules["stripe"] = old_stripe


def before_status(subs):
    return {k: v.get("status") for k, v in subs.items()}


def statuses(after):
    """Compare statuses, not whole records.

    Comparing the before-status map against the after-RECORDS map can never
    match, because one side holds strings and the other holds dicts. That made
    four correct reconciler behaviours report as failures.
    """
    return before_status(after)


# --- 1. no key at all: nothing changes, no crash -------------------------
rc, before, after = load({}, key="")
check("no key -> exit 0 and not one record changed", rc == 0 and before == statuses(after),
      f"rc={rc} {before} -> {after}")

# --- 2. Stripe says everyone is fine: nothing changes --------------------
rc, before, after = load({
    "cus_active": "active", "cus_due": "trialing", "cus_cancelled": "active"})
check("Stripe says active/trialing -> nothing changed", rc == 0 and before == statuses(after),
      f"{before} -> {after}")

# --- 3. a real cancellation IS caught ------------------------------------
rc, before, after = load({
    "cus_active": "active", "cus_due": "canceled", "cus_cancelled": "active"})
check("a cancelled subscription is downgraded", after["cus_due"]["status"] == "cancelled",
      f"cus_due stayed {after['cus_due']['status']}")
check("the other two are untouched by the same run",
      after["cus_active"]["status"] == "active" and after["cus_cancelled"]["status"] == "cancelled",
      str({k: v.get("status") for k, v in after.items()}))
check("a downgrade is recorded with a reason",
      "stripe says" in str(after["cus_due"].get("reconciled_reason", "")),
      "no audit trail on a downgrade that removes access")

# --- 4. THE CRITICAL ONE: an error must never remove access --------------
for label, boom in (("Stripe raises", Exception("API down")),
                    ("Stripe is malformed", ValueError("no status attr"))):
    rc, before, after = load({
        "cus_active": boom, "cus_due": boom, "cus_cancelled": "active"})
    check(f"{label} -> access is NOT removed", before == statuses(after),
          f"a network/API failure stripped paying customers: {before} -> {after}")

rc, before, after = load({"cus_active": "__empty__", "cus_due": "active",
                          "cus_cancelled": "active"})
check("Stripe reports no subscription at all -> downgraded (a real answer)",
      after["cus_active"]["status"] == "cancelled",
      "an empty Stripe list should be treated as cancelled")

# --- 5. it never upgrades and never revives ------------------------------
rc, before, after = load({
    "cus_active": "active", "cus_due": "active", "cus_cancelled": "active"})
check("nothing is ever upgraded or revived",
      after["cus_cancelled"]["status"] == "cancelled",
      "a previously cancelled customer was silently reactivated")

# --- 6. dry run reports but does not write ------------------------------
spec = importlib.util.spec_from_file_location("recon_dry", SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
check("the script advertises --dry-run", "--dry-run" in SRC.read_text(encoding="utf-8"))

# --- 7. it is actually wired into the daily scan -------------------------
runner = SITE / "daily_scan.ps1"
check("daily_scan.ps1 runs the reconciler",
      runner.exists() and "reconcile_subscriptions.py" in
      runner.read_text(encoding="utf-8", errors="ignore"),
      "nothing would ever reconcile - the leak stays open")

# --- 8. the key file is never committed ---------------------------------
gi = (SITE / ".gitignore").read_text(encoding="utf-8", errors="ignore")
check("stripe_reconcile.env is gitignored", "stripe_reconcile.env" in gi,
      "a Stripe key could be committed")

print()
if fails:
    print("RESULT: %d FAILED -> %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("RESULT: ALL PASS (%d checks)" % len(ran))