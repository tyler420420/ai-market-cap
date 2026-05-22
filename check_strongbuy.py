c = open('ai_earnings_scanner.py', encoding='utf-8').read()
import re
matches = list(re.finditer("'Strong Buy'", c))
print(f"Strong Buy in source: {len(matches)}")
for i, m in enumerate(matches):
    print(f"{i+1}. {c[m.start():m.start()+50]}")