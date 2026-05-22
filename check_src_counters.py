c = open('ai_earnings_scanner.py', encoding='utf-8').read()
import re

# Find ALL html += that have counter patterns
# Look for "strong_count" and "Strong Buy" in the same block
matches = list(re.finditer(r"html \+= '[^']*strong_count[^']*'", c))
print(f'Found {len(matches)} html lines with strong_count')
for m in matches:
    print(f'  Line: {c[m.start():m.start()+300]}')
    print('---')