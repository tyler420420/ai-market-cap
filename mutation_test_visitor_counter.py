"""Mutation test: prove verify_visitor_counter.py actually catches a broken counter.

A green test suite that cannot fail is decoration. This writes deliberately
broken variants of scanner_web.py to a temp dir and asserts the verifier fails
on each one. Each mutation re-instates a real defect class.

Run:  python mutation_test_visitor_counter.py
Exit 0 = every mutation was caught.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "scanner_web.py"
VERIFIER = HERE / "verify_visitor_counter.py"

BOT_LINE = '    if not ua or _BOT_RE.search(ua) or _EMPTY_UA_RE.search(ua):'
INDEXNOW_LINE = '    if request.args.get("url"):'

MUTATIONS = [
    ("bot filter disabled", BOT_LINE, "    if False:"),
    ("IndexNow pings counted", INDEXNOW_LINE, "    if False:"),
    ("static paths counted",
     "VISITOR_SKIP = ('static', 'favicon', 'robots.txt', 'sitemap', '.png', '.jpg',",
     "VISITOR_SKIP = ('/api/visitors', '/health', '/webhook')\n_UNUSED_SKIP = ('static', 'favicon', 'robots.txt', 'sitemap', '.png', '.jpg',"),
    ("POST counted as a visit", '    if request.method != "GET":', "    if False:"),
    ("dedup removed (every hit is unique)",
     "            if h not in day[\"u\"]:",
     "            day[\"u\"] = list(range(len(day[\"u\"]) + 1));  # noqa"),
    ("baseline ignored (redeploy resets all-time)",
     '    baseline = _visitor_baseline()', '    baseline = 0'),
]

results = []
for name, old, new in MUTATIONS:
    original = SRC.read_text(encoding="utf-8")
    if old not in original:
        results.append((name, False, "anchor not found - verifier is stale vs source"))
        print(f"FAIL  {name}  -- anchor not found (stale test)")
        continue
    mutated = original.replace(old, new, 1)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        shutil.copy(VERIFIER, d / VERIFIER.name)
        (d / SRC.name).write_text(mutated, encoding="utf-8")
        p = subprocess.run([sys.executable, str(d / VERIFIER.name)],
                           capture_output=True, text=True, timeout=300)
        caught = p.returncode != 0
        results.append((name, caught, f"exit={p.returncode}"))
        print(f"{'PASS' if caught else 'FAIL'}  caught: {name}  (verifier exit={p.returncode})")

print("\n" + "=" * 62)
failed = [r for r in results if not r[1]]
print(f"{len(results) - len(failed)}/{len(results)} mutations caught")
if failed:
    for n, _, d in failed:
        print(f"  MISSED: {n}  {d}")
    sys.exit(1)
print("VERIFIER BITES ON EVERY MUTATION")