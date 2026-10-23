"""Mutation proof for verify_table_columns.py.

A guard nobody has seen fail is not evidence. This reintroduces each defect
the guard claims to catch, one at a time, into throwaway copies of the
artifact and source, and requires the guard to reject every one of them
while still passing the untouched control.

Nothing here touches the real files.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
GUARD = SITE / "verify_table_columns.py"
ART_SRC = SITE / "ai_earnings_today.html"
PY_SRC = SITE / "ai_earnings_scanner.py"

art = ART_SRC.read_text(encoding="utf-8")
src = PY_SRC.read_text(encoding="utf-8")

import re as _re

assert 'data-label="3 Day Range"' not in art, "control artifact already has the defect"
# Same scope as the guard: a pipe joining a price to a percent. Other pipes
# exist legitimately (news card "Oct 23 | $318M", a headline, the methodology
# note) and must not make this control look dirty.
assert not _re.search(r"\$[\d,.]+\s*\|", art), "control artifact already has a price/percent pipe"


def m_readd_static_3day(a, s):
    """Reintroduce the 3-day column in the static rows only."""
    return a.replace('<td data-label="Price"', '<td data-label="3 Day Range">$1<br>\\u00b1 2%</td><td data-label="Price"', 1), s


def m_readd_client_3day(a, s):
    """Reintroduce it in the client re-render only -> parity drift."""
    old = """html+='<td data-label="Days" """
    new = """html+='<td data-label="3 Day Range">$1 | ±2%</td>';""" + old
    assert a.count(old) == 1
    return a.replace(old, new, 1), s


def m_readd_pipe(a, s):
    """A single price+percent cell joined by '|'."""
    return a.replace('<td data-label="Price" style="font-weight:bold">$',
                     '<td data-label="Price" style="font-weight:bold">$1 | 3%<span>', 1), s


def m_long_date(a, s):
    """One earnings cell back to 'November 4, 2026'."""
    import re
    out, n = re.subn(r'(<td data-label="Earnings">)([A-Z][a-z]{2}) (\d{1,2})',
                     lambda m: m.group(1) + {"Nov": "November", "Oct": "October"}.get(m.group(2), m.group(2)) + " " + m.group(3),
                     a, count=1)
    assert n == 1, "no short-form earnings cell to mutate"
    return out, s


def m_drop_client_cell(a, s):
    """Client renderer stops emitting a cell the static rows still emit."""
    old = """html+='<td data-label="Analysts">'+r.analysts+'</td>';"""
    assert a.count(old) == 1, "client Analysts cell not found"
    return a.replace(old, "", 1), s


def m_ragged_row(a, s):
    """The SECOND row loses a cell, so row 0 still defines the reference."""
    import re
    tbody = a.split("<tbody")[1].split("</tbody>")[0]
    rows = tbody.split("<tr")
    assert len(rows) > 3, "need at least two rows to ragged one"
    before = rows[2]
    rows[2], n = re.subn(r'<td data-label="Mkt Cap">[^<]*</td>', "", before, count=1)
    assert n == 1, "no Mkt Cap cell in row 1"
    newbody = "<tr".join(rows)
    return a.replace(tbody, newbody, 1), s


def m_months_long(a, s):
    """Source-side: months_map silently reverted to full month names."""
    assert '"11":"Nov"' in s, "months_map short form not found in source"
    return a, s.replace('"11":"Nov"', '"11":"November"', 1)


MUTANTS = [
    ("static 3-day column reappears", m_readd_static_3day),
    ("client 3-day column reappears", m_readd_client_3day),
    ("pipe separator returns", m_readd_pipe),
    ("earnings date back to long form", m_long_date),
    ("client renderer drops a cell (parity)", m_drop_client_cell),
    ("one row is ragged", m_ragged_row),
    ("months_map back to full names", m_months_long),
]

PY = sys.executable


def run(art_path, src_path):
    env = dict(os.environ, TABLE_ART=str(art_path), TABLE_SRC=str(src_path))
    p = subprocess.run([PY, str(GUARD)], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout + p.stderr


caught = 0
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    a_path, s_path = td / "art.html", td / "src.py"

    # control
    a_path.write_text(art, encoding="utf-8")
    s_path.write_text(src, encoding="utf-8")
    rc, out = run(a_path, s_path)
    print("CONTROL rc=%d %s" % (rc, "PASS" if rc == 0 else "FAIL"))
    if rc != 0:
        print(out)
        print("RESULT: control does not pass - the guard is broken, mutants prove nothing")
        sys.exit(1)
    print()

    for name, fn in MUTANTS:
        a_path.write_text(art, encoding="utf-8")
        s_path.write_text(src, encoding="utf-8")
        ma, ms = fn(art, src)
        assert (ma, ms) != (art, src), "mutant %r changed nothing - it tests nothing" % name
        a_path.write_text(ma, encoding="utf-8")
        s_path.write_text(ms, encoding="utf-8")
        rc, out = run(a_path, s_path)
        ok = rc != 0
        caught += ok
        firstfail = next((ln.strip() for ln in out.splitlines() if ln.strip().startswith("FAIL")), "")
        print("  %s  %-42s %s" % ("CAUGHT" if ok else "MISSED", name, firstfail[:70]))

print()
print("RESULT: %d/%d caught" % (caught, len(MUTANTS)))
sys.exit(0 if caught == len(MUTANTS) else 1)