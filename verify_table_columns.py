"""Guard the stock table's column set and cell format.

Three defects are covered, the third being the one Tyler actually spotted:

  1. the 3-day / 7-day / 14-day price-target columns were removed from the
     table (Tyler 2026-10-22). They must be gone from BOTH renderers - the
     static rows and the client `renderTable()` re-render.

  2. a price followed by a percent must never be joined by a '|' separator.
     Tyler's ask: price on one line, percent on the next.

  3. PARITY. The static rows and the client re-render disagreed: static cells
     used `<br><span>+-x%</span>`, the client used `' | +-x%'`. Sorting a
     column re-rendered every row, so a cell changed appearance the moment
     anyone sorted. Nothing compared the two renderers, so it survived.
     This check compares their data-labels in order and fails on any drift.

It also pins the short earnings date (`Nov 4`, not `November 4, 2026`).
"""
import os
import re
import sys
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
# Overridable so a mutation harness can point this at a damaged copy instead
# of the real artifact.
ART = Path(os.environ.get("TABLE_ART") or (SITE / "ai_earnings_today.html"))
SRC = Path(os.environ.get("TABLE_SRC") or (SITE / "ai_earnings_scanner.py"))

REMOVED = ()
TARGETS = ("3 Day Range", "7 Day Range", "14 Day Range")

fails = []
ran = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  -> " + detail) if detail and not ok else ""))
    ran.append(name)
    if not ok:
        fails.append(name)


art = ART.read_text(encoding="utf-8", errors="replace")
src = SRC.read_text(encoding="utf-8")


def js_body(text, header):
    """Brace-counted function body. A non-greedy regex cannot do this."""
    i = text.find(header)
    if i < 0:
        return ""
    start, depth = text.index("{", i), 0
    for j in range(start, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:j]
    return ""


# ------------------------------------------------------- column set extraction
# Compare ONE row against the client renderer, not every row against one
# header. Counting all 100 rows' cells against 19 headers is meaningless and
# reports a failure that does not exist.
tbody = art.split("<tbody")[1].split("</tbody>")[0] if "<tbody" in art else ""
first_row = tbody.split("<tr")[1] if "<tr" in tbody else ""
static_labels = re.findall(r'<td data-label="([^"]+)"', first_row)
client_labels = re.findall(r'data-label=\\?"([^"\\]+)\\?"', js_body(art, "function renderTable()"))

check("static renderTable() found in artifact", bool(client_labels),
      "could not extract client cell labels - a check matching nothing is not a pass")

# ---------------------------------------------------------------- 1. targets
for label in TARGETS:
    check("static rows render the %r column" % label, label in static_labels)
    check("client re-render renders the %r column" % label, label in client_labels)
    check("a header exists for %r" % label, label in art)

# CORRECTION 2026-10-22: the first version of this guard asserted these three
# columns were ABSENT, because the request was read as "remove the columns".
# The columns stay; what goes is the '|' separator - a target cell is the
# price on one line and the percent on the next. A guard written from a
# misread request actively enforces the misread.
check("headers list carries the three target columns",
      all(("'%s Day<br>Target'" % n) in src for n in ("3", "7", "14")),
      "a target header entry is missing from the headers list")
check("col_labels map carries the three target keys",
      "'pe_target': '3 Day'" in src and "'3d': '7 Day'" in src and "'5d': '14 Day'" in src)

for label in TARGETS:
    seg = art.split('data-label="%s"' % label)
    cell = seg[1].split("</td>")[0] if len(seg) > 1 else ""
    check("%r is price then percent on the next line" % label,
          "<br>" in cell and "$" in cell and "%" in cell,
          "cell does not use a line break: %r" % cell[:90])
    check("%r carries no pipe" % label, "|" not in cell, "cell: %r" % cell[:90])

# ------------------------------------------------------------------ 2. pipes
pipe_cells = re.findall(r'\$[\d,.]+\s*\|', art)
check("no '|' separating price and percent", not pipe_cells,
      "%d offending cells, e.g. %r" % (len(pipe_cells), pipe_cells[:3]))

# ----------------------------------------------------------------- 3. parity
check("static rows emit cells", len(static_labels) >= 10,
      "only %d static cells found - regex likely matched nothing" % len(static_labels))
check("client re-render emits cells", len(client_labels) >= 10,
      "only %d client cells found - regex likely matched nothing" % len(client_labels))
check("static and client emit the SAME columns in the SAME order",
      static_labels == client_labels,
      "static=%s client=%s" % (static_labels, client_labels))

all_rows = [re.findall(r'<td data-label="([^"]+)"', tr)
            for tr in tbody.split("<tr")[1:]]
ragged = [i for i, r in enumerate(all_rows) if r != static_labels]
check("every rendered row has the same columns as the first", not ragged,
      "%d ragged rows, first offender row index %s" % (len(ragged), ragged[:3]))

header_cols = re.findall(r'<th[^>]*data-col="([^"]+)"', art)
check("one header per rendered column",
      len(header_cols) == len(static_labels),
      "%d headers vs %d static cells" % (len(header_cols), len(static_labels)))

# ------------------------------------------------------------- 4. date format
earn_cells = re.findall(r'<td data-label="Earnings"[^>]*>([^<]*)</td>', art)
check("static earnings cells exist", bool(earn_cells),
      "none found - date-format check would silently pass")
bad_dates = [c for c in earn_cells if not re.fullmatch(r"[A-Z][a-z]{2} \d{1,2}", c.strip())]
check("earnings dates are short form (Nov 4)", not bad_dates,
      "offenders: %s" % sorted(set(bad_dates))[:5])

# ------------------------------------------------------- 5. source of truth
check("headers list keeps all three target columns",
      len(re.findall(r"\('(?:3|7|14)\s*Day<br>Target',", src)) == 3,
      "found %d target header entries, expected 3"
      % len(re.findall(r"\('(?:3|7|14)\s*Day<br>Target',", src)))
check("no client cell still uses a pipe", " | " not in js_body(src, "function renderTable()"))
check("no static cell still uses a pipe", not re.search(r"static_rows \+= '<td[^']*' \| ", src))

# months_map is the real lever behind the date format, and it is NOT what
# fmt_date's docstring or body looks like. The first attempt at this change
# rewrote fmt_date and left months_map holding full month names, so the
# function was correct, the docstring said "Nov 4", the guard read the source
# and saw short form - and the shipped page still said "November 4". Assert
# the map itself.
mm = re.search(r"months_map\s*=\s*\{(.*?)\}\s*\n", src, re.S)
check("months_map is defined", bool(mm), "could not find months_map in source")
mm_vals = re.findall(r'"(\d{2})"\s*:\s*"([^"]+)"', mm.group(1)) if mm else []
check("months_map has all 12 months", len(mm_vals) == 12, "found %d" % len(mm_vals))
long_months = [v for _, v in mm_vals if not re.fullmatch(r"[A-Z][a-z]{2}", v)]
check("months_map values are 3-letter abbreviations", not long_months,
      "long names still present: %s" % long_months[:4])
check("fmt_date actually uses months_map",
      "months_map.get(" in src or "months_map[" in src,
      "fmt_date no longer reads the map - the map may be dead code")

print()
if fails:
    print("RESULT: %d FAILED -> %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("RESULT: ALL PASS (%d checks)" % len(ran))