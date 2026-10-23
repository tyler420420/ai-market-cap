"""Run the full website guard suite in one process context.

Used instead of a PowerShell `cd` because the local safety policy blocks a
working-directory change in the same command as other work.
"""
import os
import subprocess
import sys
from pathlib import Path

PY = sys.executable
# Anchored to this file, not hardcoded and not the process CWD: the suite must
# be runnable from any directory, and so must every guard it spawns.
SITE = Path(__file__).resolve().parent

NAMES = [
    'verify_script_comments', 'verify_mobile_cards', 'verify_iv_real',
    'verify_table_columns', 'prove_table_columns_bites', 'verify_table_sort',
    'verify_generator_writes', 'prove_generator_writes_bites',
    'verify_paywall', 'prove_paywall_bites', 'verify_alert_targets',
    'prove_alert_targets_bites', 'verify_alert_honesty', 'verify_target_hits',
    'prove_target_hits_bites', 'verify_reconcile', 'verify_auth',
    'prove_auth_guard_bites', 'verify_output', 'prove_verify_output_bites',
    'verify_growth', 'verify_labels', 'verify_trending_cards',
    'verify_sentiment', 'verify_routes', 'verify_support_path',
    'verify_cwd_independence', 'verify_subscriber_gate',
    'verify_signup_counter', 'verify_signup_copy',
]

ok = 0
fail = []
for n in NAMES:
    p = os.path.join(SITE, n + '.py')
    if not os.path.exists(p):
        # Was a silent `continue`. Deleting a guard then made the suite
        # "pass" with a smaller count - a vanished check wearing a green
        # result, which is the exact class of lie this repo keeps paying for.
        fail.append((n, 'MISSING - listed in NAMES but not on disk'))
        continue
    # NO cwd=SITE here, deliberately. It used to be passed, which silently
    # rescued every CWD-dependent guard: run one from anywhere else and it
    # failed on a perfectly healthy tree, but inside this runner it was green.
    # Spawning each guard with whatever directory the suite was launched from is
    # what makes this suite an actual test of the invariant.
    r = subprocess.run([PY, '-X', 'utf8', p],
                       capture_output=True, text=True, errors='replace',
                       timeout=900)
    if r.returncode == 0:
        ok += 1
    else:
        fail.append((n, (r.stdout or '').strip().split('\n')[-1][:110]))

for n, tail in fail:
    print('FAIL %-30s %s' % (n, tail))
print('')
print('guards passed=%d failed=%d' % (ok, len(fail)))
sys.exit(1 if fail else 0)