import subprocess, re

# Get the old scanner code from the commit before my chat widget rebuild
result = subprocess.run(
    ['git', 'show', '6577033^:ai_earnings_scanner.py'],
    capture_output=True, text=True, encoding='utf-8', errors='replace',
    cwd=r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace'
)
old_code = result.stdout

# Find the generate_html_report function and show lines 460-490
lines = old_code.split('\n')
print('=== OLD TABLE GENERATION (lines 460-492) ===')
for i in range(459, 492):
    print(f'{i+1}: {lines[i][:120]}')