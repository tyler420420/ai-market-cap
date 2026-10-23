"""Mutation proof for verify_table_columns.py.

CORRECTION 2026-10-22: the original version of this harness reintroduced the
three target columns as defects. That was built on a misread of the request
- the columns stay and only the '|' separator goes - so those mutants are now
the CONTROL, and what counts as a defect is a column that disappears or a
pipe that comes back.

A guard written from a misread request enforces the misread, and the
mutation harness is what made that visible: it happily proved the guard
could catch a change that should never have been made.

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

assert 'data-label="3 Day Range"' in art, "control artifact is missing the 3-day column"
assert 'data-label="14 Day Range"' in art, "control artifact is missing the 14-day column"
# Same scope as the guard: a pipe joining a price to a percent. Other pipes
# exist legitimately (news card "Oct 23 | $318M", a headline, the methodology
# note) and must not make this control look dirty.
assert not _re.search(r"\$[\d,.]+\s*\|", art), "control artifact already has a price/percent pipe"


def m_drop_static_3day(a, s):
    """A target column silently disappears from the static rows."""
    out, n = _re.subn(r'<td data-label="3 Day Range">.*?</td>', "", a, count=1)
    assert n == 1, "no static 3 Day cell to remove"
    return out, s


def m_drop_client_3day(a, s):
    """...and from the client re-render too, so both agree while the column is gone."""
    out, n = _re.subn(r"""html\+='<td data-label="3 Day Range">.*?</td>';""", "", a, count=1)
    assert n == 1, "no client 3 Day cell to remove"
    return out, s


def m_readd_pipe(a, s):
    """A target cell reverts to the old ' | ' separator instead of a break."""
    old = '<br><span style="color:#00ff88">'
    assert a.count(old) >= 1, "no price-then-percent break to replace"
    return a.replace(old, "' | ", 1), s


def m_drop_header(a, s):
    """Header for a target column removed while the cells stay."""
    out, n = _re.subn(r"<th[^>]*data-col=\"3d\"[^>]*>.*?</th>", "", a, count=1)
    assert n == 1, "no 3d header to remove"
    return out, s


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
    ("static 3-day column disappears", m_drop_static_3day),
    ("client 3-day column disappears", m_drop_client_3day),
    ("3-day header disappears", m_drop_header),
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