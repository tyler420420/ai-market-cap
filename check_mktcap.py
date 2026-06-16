path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
import re
mktcaps = re.findall(r'<td data-label="Mkt Cap">([^<]+)</td>', content)
for m in mktcaps[:10]:
    print(repr(m))