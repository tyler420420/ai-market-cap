"""Guard the implied-volatility fix.

THE DEFECT
----------
The IV column displayed the same number as the 3-day P/E upside for 100 of
100 stocks. It was not a fallback and not a failed fetch - the generator
assigned the SAME expression to both fields:

    iv_from_straddle         = (straddle_cost / current_price) * 100
    post_earnings_upside_pct = (straddle_cost / current_price) * 100

A straddle premium as a percent of price is the EXPECTED MOVE, not volatility.
Labelling it "Implied Volatility" showed INTC at 3.2% when its real
pre-earnings implied volatility is near 100%.

WHAT IS ASSERTED
----------------
  1. the duplicated expression is gone from the source
  2. IV is annualised - it divides by sqrt(T) and sqrt(2/pi)
  3. it uses the expiry nearest the EARNINGS date, not the default chain
     (the default is the nearest expiry, which was TODAY for every ticker
     checked, so IV could not be computed at all)
  4. the 3/7/14 target straddle is deliberately NOT changed, so the wins on
     /wins stay reproducible
  5. an unavailable IV renders "n/a", never a bare "0%"
  6. and the real invariant, on the produced data: iv != pe_upside

Run: python verify_iv_real.py
"""
import ast
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, 'ai_earnings_scanner.py')
ART = os.path.join(HERE, 'ai_earnings_today.html')

results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok), detail))


src = io.open(GEN, encoding='utf-8', newline='').read()

# --- 1. the duplicated expression is gone ---------------------------------
check('implied_volatility is not assigned the upside expression',
      not re.search(r'implied_volatility\s*=\s*round\(\s*\(\s*straddle_cost\s*/\s*current_price\s*\)\s*\*\s*100', src),
      'IV is still the expected move')
check('the stray iv_from_straddle variable is gone',
      'iv_from_straddle' not in src,
      'iv_from_straddle was the expected-move calculation')

# --- 2. IV is annualised --------------------------------------------------
check('IV divides by sqrt(T)', 't_years ** 0.5' in src)
check('IV applies the sqrt(2/pi) straddle factor',
      '3.141592653589793' in src)
check('IV is scaled to a percentage', 'implied_volatility = round(sigma * 100, 1)' in src)

# --- 3. it uses the EARNINGS-dated expiry ---------------------------------
check('expiry is chosen nearest the earnings date',
      re.search(r'min\(future,\s*key=lambda d:\s*abs\(', src) is not None,
      'IV is still using the default nearest-expiry chain')
check('the default chain is not used for IV',
      re.search(r'days_to_exp\s*=\s*\([^)]*expiries\[0\]', src) is None,
      'IV still reads expiries[0], which was TODAY')
check('a past expiry is rejected', '>= today' in src)
check('zero days to expiry is rejected', 'days_to_exp > 0' in src)

# --- 4. targets are deliberately untouched ---------------------------------
check('target straddle still uses the default chain',
      'opt = stock.option_chain()' in src)
check('3d target formula unchanged',
      'post_earnings_3d_target = round(current_price + straddle_cost * 3, 2)' in src)
check('5d target formula unchanged',
      'post_earnings_5d_target = round(current_price + straddle_cost * 5, 2)' in src)

# --- 5. unavailable IV renders n/a, never a bare 0% -----------------------
check('static renderer guards on r.get(iv)',
      re.search(r"iv_txt = \(str\(r\['iv'\]\) \+ '%'\) if r\.get\('iv'\) else 'n/a'", src) is not None)
check('client renderer guards on r.iv',
      "(r.iv?r.iv+'%':'n/a')" in src)
# Matched against the RENDER expressions only. A plain substring search for
# "r['iv']) + '%'" also matches the new guarded static line, which is correct
# code - the check has to be about the unguarded client form specifically.
check('client renderer does not append % unconditionally',
      "r.iv+'%'</td>'" not in src)

# --- 6. THE REAL INVARIANT, on the produced artifact ----------------------
if not os.path.exists(ART):
    check('artifact exists', False, 'regenerate first')
else:
    check('artifact exists', True)
    art = io.open(ART, encoding='utf-8', newline='').read()

    def parse_rows(page):
        """Extract rowsData by brace matching.

        A non-greedy regex is not safe here: the payload embeds news URLs
        whose base64 can contain '};', so the match can stop early and the
        JSON parse fails for a reason that has nothing to do with IV.
        """
        MARKER = '<script>var rowsData='
        i = page.find(MARKER)
        if i < 0:
            return None
        ds = page[i + len(MARKER):page.find('</script>', i)]
        depth = 0
        in_str = False
        esc = False
        end = 0
        for j, ch in enumerate(ds):
            if esc:
                esc = False
                continue
            if ch == '\\':
                esc = True
                continue
            if ch == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if ch in '{[':
                depth += 1
            elif ch in '}]':
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
        return json.loads(ds[:end]) if end else None

    rows = parse_rows(art)
    if not rows:
        check('artifact rowsData is parseable', False)
    else:
        both = [r for r in rows if r.get('iv') and r.get('pe_upside')]
        same = [r for r in both if r.get('iv') == r.get('pe_upside')]
        check('artifact rowsData is parseable', True)
        check('no row has iv == pe_upside', not same,
              '%d rows still match, e.g. %s'
              % (len(same), [(r['ticker'], r['iv'], r['pe_upside']) for r in same[:3]]))

        have = [r['iv'] for r in rows if r.get('iv')]
        check('IV is populated for most rows',
              len(have) >= len(rows) * 0.5,
              'only %d/%d rows have an IV' % (len(have), len(rows)))
        plausible = [v for v in have if 10 <= v <= 250]
        check('IV values land in a plausible band',
              len(plausible) >= len(have) * 0.8,
              'implausible: %s' % sorted(set(v for v in have if not 10 <= v <= 250))[:8])

        # A row with no IV must render "n/a", never "0%".
        check('rows without IV are marked n/a, not 0%',
              re.search(r'data-label="IV"[^>]*>n/a<', art) is not None
              or not any(not r.get('iv') for r in rows),
              'a row has no IV but no n/a appears in the markup')

        if not same and have:
            r0 = rows[0]
            print('\nsample: %s iv=%s pe_upside=%s price=%s'
                  % (r0.get('ticker'), r0.get('iv'), r0.get('pe_upside'), r0.get('price')))

# --- 7. generator still parses --------------------------------------------
try:
    ast.parse(src)
    check('generator still parses', True)
except SyntaxError as e:
    check('generator still parses', False, str(e))

fails = sum(1 for _, ok, _ in results if not ok)
for n, ok, d in results:
    print('%-4s %s%s' % ('PASS' if ok else 'FAIL', n, (' - ' + d) if d and not ok else ''))
print('')
print('%d/%d checks passed' % (len(results) - fails, len(results)))
sys.exit(1 if fails else 0)