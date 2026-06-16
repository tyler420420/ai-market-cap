path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find renderTable section
idx = content.find('renderTable()')
seg = content[idx:idx+3000]

# Find all td patterns
import re
# Find html+= patterns
tds = re.findall(r"html\+=.'<td([^>]+)>(.*?)'.", seg, re.DOTALL)
print(f'TD patterns in JS: {len(tds)}')
for attr, inner in tds:
    print(f'ATTR: {attr[:80]}')
    print(f'INNER: {inner[:60]}')
    print()