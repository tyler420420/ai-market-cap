"""Mutation proof for verify_alert_targets.py.

Reintroduces the leak - and four ways of half-fixing it - one at a time, into
a throwaway copy of the sender, and requires the guard to reject every one.

Nothing here touches the real file. Each mutant is written to a temp dir
together with its own scanner_data.json, because build_email() loads data
from Path(__file__).parent. Without that copy every mutant would "fail" for
the wrong reason (no data), which would prove nothing.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
GUARD = SITE / "verify_alert_targets.py"
DATA = SITE / "scanner_data.json"

src = SITE.joinpath("send_daily_alert.py").read_text(encoding="utf-8")
PY = sys.executable

assert "if paid:" in src, "control already leaks - fix the real file first"


def m_ignore_paid(s):
    """The original defect: the tier flag is accepted and never consulted."""
    return s.replace("        if paid:\n            for key, label in zip(PAID_COLUMNS, PAID_LABELS):\n"
                     "                if s.get(key):\n"
                     "                    d.append(f\"{label} {money(s[key])}\")\n",
                     "        for key, label in zip(PAID_COLUMNS, PAID_LABELS):\n"
                     "            if s.get(key):\n"
                     "                d.append(f\"{label} {money(s[key])}\")\n")


def m_no_targets_at_all(s):
    """Over-corrected: the paywall is 'fixed' by removing the product."""
    return s.replace("        if paid:\n            for key, label in zip(PAID_COLUMNS, PAID_LABELS):",
                     "        if False:\n            for key, label in zip(PAID_COLUMNS, PAID_LABELS):")


def m_paid_also_gated(s):
    """build_variants hands BOTH keys the teaser.

    The first attempt at this mutant edited the `targets =` line into
    `if (d and paid)`, which was semantically identical to the real code -
    when paid is False the loop already produced an empty list - so the guard
    correctly passed it. The downgrade has to happen where the tier is
    assigned to a recipient, not where the targets are rendered.
    """
    return s.replace("        html, subject = build_email(paid=paid)",
                     "        html, subject = build_email(paid=False)")


def m_paid_columns_dead(s):
    """PAID_COLUMNS defined but no longer referenced - the original smell."""
    return s.replace("for key, label in zip(PAID_COLUMNS, PAID_LABELS):",
                     'for key, label in zip(("pe_target", "3d", "5d"), ("3d", "7d", "14d")):')


def m_both_transports(s):
    """Every recipient gets two copies of the same email."""
    return s.replace("        try:\n            _send(env, email, subj, html)\n",
                     "        try:\n            send_via_api(env, email, subj, html)\n"
                     "            send_via_smtp(env, email, subj, html)\n            _send(env, email, subj, html)\n")


def m_upsell_swapped(s):
    """Subscriber sent to the pricing page."""
    return s.replace('cta_href = "https://aismarketcap.com"\n', 'cta_href = "https://aismarketcap.com/pricing"\n')


MUTANTS = [
    ("paid flag ignored (the original leak)", m_ignore_paid),
    ("targets removed for BOTH tiers", m_no_targets_at_all),
    ("subscriber variant downgraded", m_paid_also_gated),
    ("PAID_COLUMNS decorative again", m_paid_columns_dead),
    ("both transports called per recipient", m_both_transports),
    ("subscriber upsold to /pricing", m_upsell_swapped),
]

assert DATA.exists(), "scanner_data.json is required to run the behavioural half"


def run(path):
    env = dict(os.environ, ALERT_SRC=str(path))
    p = subprocess.run([PY, str(GUARD)], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout + p.stderr


caught = 0
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    shutil.copy2(DATA, td / "scanner_data.json")
    target = td / "send_daily_alert.py"

    target.write_text(src, encoding="utf-8")
    rc, out = run(target)
    print("CONTROL rc=%d %s" % (rc, "PASS" if rc == 0 else "FAIL"))
    if rc != 0:
        print(out)
        print("RESULT: control does not pass - the guard proves nothing")
        sys.exit(1)
    print()

    for name, fn in MUTANTS:
        mut = fn(src)
        assert mut != src, "mutant %r changed nothing - it tests nothing" % name
        target.write_text(mut, encoding="utf-8")
        rc, out = run(target)
        ok = rc != 0
        caught += ok
        first = next((ln.strip() for ln in out.splitlines()
                      if ln.strip().startswith("FAIL")), "(guard passed)")
        print("  %s  %-42s %s" % ("CAUGHT" if ok else "MISSED", name, first[:66]))

print()
print("RESULT: %d/%d caught" % (caught, len(MUTANTS)))
sys.exit(0 if caught == len(MUTANTS) else 1)