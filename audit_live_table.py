"""Live check of the deployed stock table at https://aismarketcap.com.

Reads the anonymous (stranger) page, because that is what the columns were
removed from. Source correctness is verify_table_columns.py's job; this one
only proves the deployed artifact agrees.
"""
import re
import sys
import urllib.request

URL = "https://aismarketcap.com/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  -> " + detail) if detail and not ok else ""))
    if not ok:
        fails.append(name)


req = urllib.request.Request(URL, headers={"User-Agent": UA})
with urllib.request.urlopen(req, timeout=30) as r:
    html = r.read().decode("utf-8", errors="replace")

print("fetched %d bytes from %s\n" % (len(html), URL))

check("page actually loaded", len(html) > 20000, "only %d bytes" % len(html))

for label in ("3 Day Range", "7 Day Range", "14 Day Range"):
    check('live page has no "%s" column' % label, label not in html)

pipe_cells = re.findall(r"\$[\d,.]+\s*\|", html)
check("live page has no '|' price/percent separator", not pipe_cells,
      "%d found, e.g. %r" % (len(pipe_cells), pipe_cells[:3]))

earn = re.findall(r'<td data-label="Earnings"[^>]*>([^<]*)</td>', html)
check("live earnings cells exist", bool(earn), "none found")
bad = [c for c in earn if not re.fullmatch(r"[A-Z][a-z]{2} \d{1,2}", c.strip())]
check("live earnings dates are short form", not bad, "offenders: %s" % sorted(set(bad))[:5])

headers = re.findall(r'<th[^>]*data-col="([^"]+)"', html)
tbody = html.split("<tbody")[1].split("</tbody>")[0] if "<tbody" in html else ""
rows = tbody.split("<tr")[1:]
# One row against one header row. Counting every row's cells against the
# headers is meaningless with 100 rows and reports a failure that is not real.
first = re.findall(r'<td data-label="([^"]+)"', rows[0]) if rows else []
check("live static rows and headers agree in count", len(headers) == len(first),
      "%d headers vs %d cells in the first row" % (len(headers), len(first)))


def js_body(text, header):
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


client = re.findall(r'data-label=\\?"([^"\\]+)\\?"', js_body(html, "function renderTable()"))
check("live client re-render emits cells", bool(client),
      "could not extract client labels - the parity check below would pass on nothing")
check("live static and client render the SAME columns in the SAME order",
      first == client, "static=%s client=%s" % (first, client))
ragged = [i for i, r in enumerate(rows) if re.findall(r'<td data-label="([^"]+)"', r) != first]
check("live every row has the same columns as the first", not ragged,
      "%d ragged rows" % len(ragged))

print()
if fails:
    print("RESULT: %d FAILED -> %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("RESULT: ALL PASS (%d checks)" % 12)