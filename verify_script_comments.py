"""Guard against a // comment silently swallowing JavaScript.

THE BUG THIS CAUGHT
-------------------
The generator emits its CSS and JS as a run of single-line Python strings:

    html += '<script>'
    html += '// Gate: remove pro-gate overlay if subscriber'
    html += 'if(window.__isSubscriber){ ... }else{ ... }'

Concatenated, the page contained one line:

    // Gate: remove pro-gate overlay if subscriberif(window.__isSubscriber){...}

A // comment runs to end-of-line. There were zero newlines in the whole
433-byte script, so JavaScript treated ALL of it as a comment and the gate
never ran. In production that meant:

  * subscribers were served the blurred paywall over their own entry,
    targets and stop;
  * non-subscribers never got `body.nonsub`, so every mobile rule keyed on
    it silently did nothing;
  * the Pro Scan -> Refresh swap never happened, for anyone.

It type-checked, it parsed as Python, every content guard passed, and the
CSS was verifiably in the media query. Nothing else could have caught it.

THE RULE
--------
Inside any <script> block, a // comment must be followed by a newline before
any real code. Same for <!-- in old-style scripts. A block comment /* ... */
is fine without a newline.

Run: python verify_script_comments.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, 'ai_earnings_today.html')

results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok), detail))


if not os.path.exists(ART):
    print('FAIL artifact missing - regenerate first')
    sys.exit(1)

art = open(ART, encoding='utf-8', newline='').read()

# Pull every inline script body.
scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', art,
                     re.S | re.I)
check('inline scripts found', len(scripts) > 0, '%d blocks' % len(scripts))

# A // comment that is not terminated by a newline before the end of its
# script block, AND is followed by code-looking text, is a swallowed script.
swallowed = []
for idx, body in enumerate(scripts):
    for ln_no, line in enumerate(body.split('\n')):
        pos = line.find('//')
        if pos == -1:
            continue
        # ignore 'http://' inside a string - not a comment
        if line[max(0, pos - 1):pos] == ':':
            continue
        rest = line[pos + 2:].strip()
        if not rest:
            continue                      # whole-line comment, fine
        # code after // on the same line == the comment eats it
        if re.match(r'^(if|var|function|window|document|else|for|\}|\{)',
                    rest):
            swallowed.append((idx, ln_no, rest[:70]))

check('no // comment swallows following code', not swallowed,
      '%d swallowed: %s' % (len(swallowed), swallowed[:3]))

# The specific gate that was dead.
gate = None
for body in scripts:
    if 'pro-gate' in body:
        gate = body
        break
check('the subscriber gate script is present', gate is not None)
if gate is not None:
    first = gate.lstrip().split('\n')[0]
    check('gate header is a block comment, not //',
          not first.startswith('//'),
          'starts with // again: %r' % first[:60])
    check('gate header line contains no code after the comment',
          'if(window.__isSubscriber)' not in first,
          'code is on the comment line')
    check('gate actually executes the subscriber branch',
          'if(window.__isSubscriber)' in gate)
    check('gate actually executes the non-subscriber branch',
          'classList.add("nonsub")' in gate)
    check('gate removes the overlay for subscribers',
          re.search(r'getElementById\("pro-gate"\).*?display\s*=\s*"none"',
                    gate, re.S) is not None)
    check('gate relabels the button for subscribers',
          'sb.textContent="Refresh"' in gate)

fails = sum(1 for _, ok, _ in results if not ok)
for n, ok, d in results:
    print('%-4s %s%s' % ('PASS' if ok else 'FAIL', n, (' - ' + d) if d and not ok else ''))
print('')
print('%d/%d checks passed' % (len(results) - fails, len(results)))
sys.exit(1 if fails else 0)