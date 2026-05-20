import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines[:60], 1):
    sys.stdout.write(str(i) + ': ' + l)