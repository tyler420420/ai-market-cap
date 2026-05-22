c = open('ai_earnings_today.html', encoding='utf-8').read()
# Check for max-width
import re
matches = re.findall(r'max-width[^"]*"[^"]*"', c)
for m in matches[:5]:
    print(m)