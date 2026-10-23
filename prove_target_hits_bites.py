"""Mutation proof for verify_target_hits.py.

verify_target_hits.py drives the nudge with bad PAYLOADS. This mutates the
SOURCE - the harder case: would the guard notice if someone rewrote the
nudge to render unconditionally, to dress up a stale hit, or to print a price
that is not in the tracked file?

A MUTANT THAT CRASHES THE GUARD IS NOT A CATCH.
---------------------------------------------
The first version of this harness reported 4/4 while three of its mutants
had merely made the guard raise. A guard that cannot execute catches nothing -
it proves only that broken code breaks. Every mutant below is written to be
syntactically valid and semantically wrong, and the runner explicitly
separates "a check failed" from "the guard died", counting only the former.

Nothing here touches the real file.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
GUARD = SITE / "verify_target_hits.py"
WEB = SITE / "scanner_web.py"

src = WEB.read_text(encoding="utf-8")
PY = sys.executable

assert "def _live_hit_nudge(" in src, "control is missing the nudge entirely"
assert '(h.get("days_to_hit") or 999) <= fresh_days' in src, \
    "control already ignores freshness - fix the real file first"


def _swap(s, old, new, label):
    assert s.count(old) == 1, "%s: anchor matched %d times, need exactly 1" % (
        label, s.count(old))
    return s.replace(old, new, 1)


def m_ignore_freshness(s):
    """A 3-month-old hit gets presented as 'JUST HIT TARGET'."""
    return _swap(s, '(h.get("days_to_hit") or 999) <= fresh_days', "True",
                 "ignore_freshness")


def m_always_render(s):
    """Renders a confident banner even when there is no hit at all."""
    return _swap(
        s,
        "    if not fresh:\n        return ''",
        "    if not fresh:\n"
        "        fresh = [{'ticker': 'FAKE', 'target': 999.0, 'current': 1000.0,"
        " 'vs_target_pct': 0.1, 'date': '2026-10-22', 'days_to_hit': 0}]",
        "always_render")


def m_inflate_prices(s):
    """Every rendered price is 1.5x the real one."""
    return _swap(s, 'return f"{float(v):,.2f}"', 'return f"{float(v)*1.5:,.2f}"',
                 "inflate_prices")


def m_unverified_json(s):
    """A corrupt file takes the pricing page down instead of rendering blank."""
    return _swap(
        s,
        '        print(f"[Targets] nudge unavailable: {e}")\n        return \'\'',
        '        print(f"[Targets] nudge unavailable: {e}")\n        raise',
        "unverified_json")


MUTANTS = [
    ("nudge ignores freshness", m_ignore_freshness),
    ("nudge renders with no hits", m_always_render),
    ("nudge inflates every price", m_inflate_prices),
    ("corrupt JSON takes the page down", m_unverified_json),
]


def run(web_path):
    env = dict(os.environ, WEB_SRC=str(web_path))
    p = subprocess.run([PY, str(GUARD)], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout + p.stderr


caught = crashed = 0
with tempfile.TemporaryDirectory() as td:
    target = Path(td) / "scanner_web.py"

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

        # A guard that DIED is not a catch. Only a reported FAIL is.
        died = ("Traceback (most recent call last)" in out) or ("SyntaxError" in out)
        first = next((ln.strip() for ln in out.splitlines()
                      if ln.strip().startswith("FAIL")), "")
        if rc != 0 and not died and first:
            caught += 1
            verdict = "CAUGHT"
        elif died:
            crashed += 1
            verdict = "CRASHED - not a valid catch"
        else:
            crashed += 1
            verdict = "MISSED - guard passed"

        print("  %-9s %-34s %s" % (verdict, name, first[:58]))

print()
print("RESULT: %d/%d caught (%d invalid)" % (caught, len(MUTANTS), crashed))
sys.exit(0 if caught == len(MUTANTS) else 1)