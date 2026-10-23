"""Guard the mobile card redesign against regression.

WHY THIS FILE EXISTS
--------------------
The card design is pure CSS keyed on :nth-child. That makes both the static
generator and the client-side renderTable() get restyled at once, by
construction - which is the whole reason it was chosen. The cost of that
choice is that the layout's correctness depends on the COLUMN ORDER of the
markup, not on any class name. If a column is ever inserted, removed or
reordered, the design silently keeps applying to whatever now sits in that
position: the score badge would land on the price, the three target boxes
would show analysts/s-buy/mkt-cap, and nothing would error.

So this guard asserts the thing CSS actually depends on.

It also guards a misread that already happened once today: the 3/7/14-day
target columns were deleted when only the pipe separator needed removing.
Column count and order are therefore asserted explicitly, so a future
"cleanup" cannot quietly delete the very cells paying customers came for.

WHAT IS ASSERTED
----------------
  1. the produced ARTIFACT carries the card design (not just the source)
  2. static rows and client renderTable() agree on column order
  3. the three target columns exist, in positions 7/8/9
  4. the label stack that made the table unreadable is actually disabled
  5. price and percent still break onto separate lines on mobile
  6. the More toggle exists, is wired, and re-arms after a re-render
  7. the artifact is NEWER than the generator that produces it

Run: python verify_mobile_cards.py
"""
import ast
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, 'ai_earnings_scanner.py')

EXPECTED_ORDER = [
    'Ticker', 'Company', 'Score', 'Earnings', 'Days', 'Price',
    '3 Day Range', '7 Day Range', '14 Day Range',
    'Analysts', 'Strong Buy', 'Buy', 'Hold', 'Sell', 'Mkt Cap',
    'Shorts', 'IV', 'Sentiment', 'News',
]

results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok), detail))


src = io.open(GEN, encoding='utf-8', newline='').read()

# --- 1. locate the produced artifact ---------------------------------------
cands = [f for f in os.listdir(HERE)
         if re.match(r'ai_earnings_(today|57day_\d+)\.html$', f)]
check('artifact exists', bool(cands),
      '' if cands else 'no ai_earnings_today.html in %s' % HERE)
if not cands:
    for n, ok, d in results:
        print('%-4s %s %s' % ('PASS' if ok else 'FAIL', n, d))
    sys.exit(1)

ART = os.path.join(HERE, 'ai_earnings_today.html')
art = io.open(ART, encoding='utf-8', newline='').read()

# --- 2. the artifact is newer than the generator ---------------------------
check('artifact is newer than generator',
      os.path.getmtime(ART) >= os.path.getmtime(GEN),
      'regenerate before trusting this guard')

# --- 3. the card design reached the ARTIFACT, not just the source ---------
check('artifact: card is a grid (deterministic rows)',
      '#stockTable tbody tr{display:grid' in art)
check('artifact: six-column track so tiles are always equal',
      'grid-template-columns:repeat(6,1fr)' in art)
check('artifact: 19-row label stack disabled',
      '#stockTable td::before{content:none!important}' in art)
check('artifact: old stack rule (justify-content:space-between) is gone',
      'td{display:flex;justify-content:space-between' not in art)
check('artifact: old br-hiding rule is gone',
      '#stockTable td>br{display:none}' not in art)
check('artifact: no leftover flex sizing on the row',
      '#stockTable tbody tr{display:flex' not in art)
check('artifact: badge sits in the last column, not absolute',
      '#stockTable td:nth-child(3){grid-column:6' in art and
      'td:nth-child(3){position:absolute' not in art)

# --- 3b. every cell must have an explicit grid placement ------------------
# The whole point of grid over flex is that the layout is STATED. A cell
# with no grid-column/grid-row silently falls back to auto-placement, which
# is exactly the bug the flex attempts had.
for sel, row in (
        ('td:first-child{grid-column:1/6;grid-row:1', 1),
        ('td:nth-child(2){grid-column:1/7;grid-row:2', 2),
        ('td:nth-child(3){grid-column:6;grid-row:1', 1),
        ('td:nth-child(4){grid-column:1/3;grid-row:3', 3),
        ('td:nth-child(5){grid-column:3/5;grid-row:3', 3),
        ('td:nth-child(6){grid-column:5/7;grid-row:3', 3),
        ('td:nth-child(7){grid-column:1/3;grid-row:4', 4),
        ('td:nth-child(8){grid-column:3/5;grid-row:4', 4),
        ('td:nth-child(9){grid-column:5/7;grid-row:4', 4),
        ('td:nth-child(10){grid-column:1/2;grid-row:5', 5),
        ('td:nth-child(11){grid-column:2/3;grid-row:5', 5),
        ('td:nth-child(16){grid-column:3/4;grid-row:5', 5),
        ('td:nth-child(17){grid-column:4/6;grid-row:5', 5)):
    check('artifact: cell has explicit placement - ' + sel.split('{')[0][3:], sel in art)
check('artifact: the three tiles each span 2 of 6 columns (equal thirds)',
      art.count('grid-row:4') == 3)
check('artifact: More button is a grid item on row 5',
      '.mob-more{grid-column:6;grid-row:5' in art)

# --- 4. price and percent must not jam together on mobile -----------------
# These selectors are comma-grouped in the shipped CSS, so the check must
# not require a '{' straight after the selector.
for n, pos in (('3', 7), ('7', 8), ('14', 9)):
    check('artifact: %s-day target keeps its line break' % n,
          ('#stockTable td:nth-child(%d)>br' % pos) in art)
    check('artifact: %s-day target box is labelled' % n,
          ("td:nth-child(%d)::before{content:'%s DAY'" % (pos, n)) in art)
check('artifact: the three target boxes share one line-break rule',
      '#stockTable td:nth-child(7)>br,#stockTable td:nth-child(8)>br,'
      '#stockTable td:nth-child(9)>br{display:block!important}' in art)
check('artifact: tile labels are short enough not to wrap',
      'white-space:nowrap' in art)

# --- 5. the More toggle ---------------------------------------------------
check('artifact: hidden columns start collapsed',
      'font-size:.78em!important;color:#8b949e;display:none}' in art)
check('artifact: .open restores them',
      '#stockTable tbody tr.open td:nth-child(12)' in art)
check('artifact: every hidden cell gets an open-state row',
      all(('tr.open td:nth-child(%d){grid-column' % i) in art
          for i in (12, 13, 14, 15, 18, 19)))
check('artifact: addMobileMore shipped', 'function addMobileMore(){' in art)
check('artifact: re-arms after a client re-render',
      'tbody.innerHTML=html;addMobileMore();' in art)
check('artifact: runs on load', "window.addEventListener('load',addMobileMore)" in art)
check('artifact: runs on resize/orientation change',
      "window.addEventListener('resize',addMobileMore)" in art)
check('artifact: only one copy of addMobileMore (idempotent inject)',
      art.count('function addMobileMore(){') == 1,
      'found %d' % art.count('function addMobileMore(){'))
check('artifact: helper defined before it is called',
      art.index('function addMobileMore(){') < art.index('addMobileMore();}'))

# --- 6. static rows and client renderTable MUST agree on column order -----
def data_labels(text):
    """Labels in document order.

    The client renderer lives inside a double-quoted Python string, so its
    attributes appear escaped in the source (data-label=\\"Ticker\\") while
    the static rows are plain HTML. The optional backslash matches both.
    """
    return re.findall(r'data-label=\\?"([^"\\]+)\\?"', text)


# static generator rows
gen_rows = src[src.index('static_rows = \'\''):src.index('html += static_rows')]
static = data_labels(gen_rows)
check('static generator emits 19 cells per row', len(static) == 19,
      'got %d' % len(static))
check('static generator column order is correct', static == EXPECTED_ORDER,
      'got %s' % static)

# client renderTable(). The search for the closing tag must start AT
# renderTable, otherwise it finds the first </script> in the file - which is
# far earlier - and silently yields an empty slice.
_js_start = src.index('function renderTable(){')
js = src[_js_start:src.index('</script>', _js_start)]
client = data_labels(js)
check('client renderTable emits 19 cells per row', len(client) == 19,
      'got %d' % len(client))
check('client renderTable column order is correct', client == EXPECTED_ORDER,
      'got %s' % client)
check('static and client column order agree',
      static == client,
      'static != client - sorting a column would restyle every row')

# --- 7. the target columns still exist (the misread guard) ----------------
for lbl in ('3 Day Range', '7 Day Range', '14 Day Range'):
    check('target column %r still present in static rows' % lbl,
          lbl in static)
    check('target column %r still present in client rows' % lbl,
          lbl in client)
check('no pipe separator left in client target cells',
      "' | '" not in js and "&#124;" not in js)

# --- 7b. fixes that came out of the CTO review ---------------------------
# The desktop price column carries a green border-right + glow to separate
# "price now" from "targets". On a grid card that reads as a stray green
# box, so it must be neutralised on mobile and PRESERVED on desktop.
check('artifact: green price divider suppressed on mobile',
      'border-right:0!important;box-shadow:none!important}' in art)
check('desktop keeps the green price divider',
      'td:nth-child(6){border-right:2px solid #3fb950' in art)
# Company names were truncated to 12 characters in the DATA, so every
# renderer inherited the cut: "Palo Alto Ne", "NVIDIA Corpo",
# "ServiceNow,". Truncation belongs at render time, not in the payload.
check('company name is no longer truncated in the payload',
      'company_name[:12]' not in src and 'company_name' in src)
check('static renderer truncates with an ellipsis instead',
      "co_name = (cn[:18] + '...') if len(cn) > 18 else cn" in src)
check('news still renders through the helper, never a raw dict',
      'newsHtml(r.news)' in src and 'news_link(r[' in src)

# --- 8. desktop must be untouched by a mobile-only change -----------------
check('desktop table CSS untouched (mobile rules stay in the query)',
      art.index('@media(max-width:768px)') <
      art.index('#stockTable tbody tr{display:grid'))
check('thead still hidden on mobile (unchanged behaviour)',
      '#stockTable thead{display:none}' in art)
check('the redesign does NOT pin the page width',
      'body{width:390px' not in art and 'body style="width:390px"' not in art,
      'a hardcoded 390px body makes every narrower phone scroll sideways')

# --- 9. the generator must still parse ------------------------------------
try:
    ast.parse(src)
    check('generator still parses', True)
except SyntaxError as e:
    check('generator still parses', False, str(e))

# --- report ---------------------------------------------------------------
fails = 0
for n, ok, d in results:
    if not ok:
        fails += 1
    print('%-4s %s%s' % ('PASS' if ok else 'FAIL', n, (' - ' + d) if d else ''))
print('')
print('%d/%d checks passed' % (len(results) - fails, len(results)))
sys.exit(1 if fails else 0)