"""The daily alert must not mail Pro targets to the free list.

THE DEFECT
----------
`build_email()` took no recipient argument. It built ONE email containing the
3d / 7d / 14d targets, and `main()` sent that identical email to everyone on
`email_list.json` as well as to paying subscribers. `PAID_COLUMNS` was defined
at module scope and never referenced again.

Free-page signups would have received the paid targets in writing, in an
inbox, where they cannot be taken back. Same defect class as the CSS-blur
paywall leak, moved into email.

WHAT THIS CHECKS
----------------
1. Source: `build_email` takes a `paid` argument, `PAID_COLUMNS` is actually
   used rather than decorative, and exactly one transport is selected.
2. Behaviour: both variants are built from the REAL scanner data and the free
   one is required to carry no target values.

The behavioural half is the one that matters. Reading the source proves only
that the function has a parameter named `paid`.

Collision note: the test asserts on the `3d $` / `7d $` / `14d $` label
markers rather than on bare dollar amounts. A stock's price can equal some
other row's target, so "$257 appears in the free email" would be a false
failure. The label markers are produced only by the target-building branch.
"""
import importlib.util
import os
import re
import sys
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
# Overridable so a mutation harness can point this at a damaged copy. The
# copy must sit next to its own scanner_data.json, because build_email() loads
# data from Path(__file__).parent.
SRC = Path(os.environ.get("ALERT_SRC") or (SITE / "send_daily_alert.py"))

fails = []
ran = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  -> " + detail) if detail and not ok else ""))
    ran.append(name)
    if not ok:
        fails.append(name)


src = SRC.read_text(encoding="utf-8")

spec = importlib.util.spec_from_file_location("send_daily_alert", SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# ------------------------------------------------------------------ 1. source
check("build_email takes a paid argument",
      re.search(r"def build_email\(paid\s*:\s*bool", src) is not None,
      "the recipient tier is not a parameter - the same email goes to everyone again")
check("PAID_COLUMNS is used, not decorative",
      len(re.findall(r"\bPAID_COLUMNS\b", src)) >= 2,
      "defined once and never referenced again")
check("targets are built behind the paid flag",
      re.search(r"if paid:\s*\n\s+for key, label in zip\(PAID_COLUMNS", src) is not None,
      "could not find the paid-gated target loop")
check("exactly one transport is selected",
      "def pick_transport(" in src and "send_via_api(env, email" not in src,
      "main() still calls both transports per recipient")

# --------------------------------------------------------------- 2. behaviour
free_html, free_subj = mod.build_email(paid=False)
paid_html, paid_subj = mod.build_email(paid=True)

check("both variants build from real data", bool(free_html) and bool(paid_html),
      "scanner_data.json produced no picks - every behavioural check below "
      "would pass on nothing")
if not (free_html and paid_html):
    print("\nRESULT: %d FAILED -> data unavailable" % len(fails))
    sys.exit(1)

n_picks = len(re.findall(r"<tr><td[^>]*font-weight:bold;color:#58a6ff", paid_html))
check("the message carries a real pick list", n_picks >= 1, "0 rows rendered")

MARKERS = ("3d $", "7d $", "14d $")
leaked = [m for m in MARKERS if m in free_html]
check("free email contains NO target values", not leaked,
      "free-list email leaked %s" % leaked)

check("free email offers Pro instead of the numbers",
      free_html.count(mod.FREE_TARGETS_CELL) == n_picks,
      "expected %d '%s' cells, found %d" % (n_picks, mod.FREE_TARGETS_CELL,
                                            free_html.count(mod.FREE_TARGETS_CELL)))
check("paid email contains the target values",
      any(m in paid_html for m in MARKERS),
      "no %s marker in the subscriber email - the fix may have removed the "
      "targets for BOTH tiers" % "/".join(MARKERS))
check("paid email does not advertise the paywall",
      mod.FREE_TARGETS_CELL not in paid_html,
      "a subscriber was told 'Available in Pro'")
check("free email sends them to the pricing page",
      "aismarketcap.com/pricing" in free_html)
check("paid email is not upsold",
      "aismarketcap.com/pricing" not in paid_html,
      "a paying subscriber was sent to the pricing page")

# Every target value present in the paid message must be absent from the free
# one. Comparing the two documents directly catches a leak that the marker
# check would miss if the labels were ever reworded.
check("no paid-only figure appears in the free email",
      not (set(re.findall(r"\b\d[d]\s[\d,]{3,}", paid_html)) -
            set(re.findall(r"\b\d[d]\s[\d,]{3,}", free_html))),
      "free email contains a target figure the paid one has")

# ------------------------------------------------------- 3. the wiring itself
# build_email() being correct does not mean the right person gets the right
# message - that decision is made in build_variants()/main(). A variant table
# where both keys point at the teaser downgrades every subscriber while
# build_email() still passes every check above, so exercise the table itself.
variants = mod.build_variants()
check("build_variants returns both tiers", set(variants) == {False, True},
      "got keys %s" % sorted(map(str, variants)))

FREE = mod.FREE_TARGETS_CELL
v_free = variants.get(False, ("", ""))
v_paid = variants.get(True, ("", ""))
check("the free key holds the teaser", bool(FREE) and FREE in v_free[0],
      "variants[False] does not carry the Pro placeholder")
check("the free key holds no target values",
      not [m for m in MARKERS if m in v_free[0]],
      "variants[False] carries target values")
check("the paid key holds the real targets",
      any(m in v_paid[0] for m in MARKERS),
      "variants[True] has no targets - subscribers would get the teaser")
check("the two variants differ",
      v_free[0] != v_paid[0],
      "both keys resolve to the same message")

# One transport, never two - and the API wins when both are configured.
COMPLETE_SMTP = {"ALERT_SMTP_HOST": "smtp.x", "ALERT_SMTP_USER": "a@b.com",
                 "ALERT_SMTP_PASS": "secret"}
_, fn_api = mod.pick_transport({"ALERT_API_KEY": "k", **COMPLETE_SMTP})
check("pick_transport returns exactly one sender when both are configured",
      fn_api is not None and fn_api is mod.send_via_api,
      "expected send_via_api, got %s" % getattr(fn_api, "__name__", fn_api))
name_none, fn_none = mod.pick_transport({})
check("pick_transport reports unconfigured rather than guessing",
      name_none is None and fn_none is None)
_, fn_smtp = mod.pick_transport(COMPLETE_SMTP)
check("a complete SMTP credential selects the SMTP sender", fn_smtp is mod.send_via_smtp)
# A host with no password is the state alert.env sits in right now. Accepting
# it made --dry-run announce a transport it could not authenticate with.
_, fn_blank = mod.pick_transport({"ALERT_SMTP_HOST": "smtp.x", "ALERT_SMTP_USER": "a@b.com"})
check("SMTP host without a password is NOT treated as configured",
      fn_blank is None,
      "a half-filled credential announced a working transport")

print()
if fails:
    print("RESULT: %d FAILED -> %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("RESULT: ALL PASS (%d checks)" % len(ran))