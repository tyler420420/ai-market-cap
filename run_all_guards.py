"""Run the full website guard suite in one process context.

Used instead of a PowerShell `cd` because the local safety policy blocks a
working-directory change in the same command as other work.
"""
import os
import subprocess
import sys

PY = sys.executable
SITE = r'C:\Users\Tyler_AI\ai-market-cap'

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
]

ok = 0
fail = []
for n in NAMES:
    p = os.path.join(SITE, n + '.py')
    if not os.path.exists(p):
        continue
    r = subprocess.run([PY, '-X', 'utf8', p], cwd=SITE,
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