with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find all occurrences of th[data-col
import re
for m in re.finditer(r'th\[data-col=[^]]+', c):
    print(repr(c[m.start()-20:m.start()+40]))
    print('---')