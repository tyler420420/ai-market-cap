path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find("html+='<tr style")
end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
seg = content[start:end]

print(f'Segment length: {len(seg)}')
# Find all <td> patterns
import re
tds = re.findall(r'<td([^>]*)>', seg)
print(f'Total td: {len(tds)}')
for t in tds:
    has = 'data-label' in t
    print(f'  label={\"YES\" if has else \"NO\"} attr={repr(t[:60])}')