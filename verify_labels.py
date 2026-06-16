path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Count data-labels in JS renderTable section
idx = content.find('renderTable()')
seg = content[idx:idx+4000]

import re
# Find all html+= patterns with td
tds = re.findall(r"html\+=.'<td([^>]*)(?:>|/?>)(.*?)'.;", seg, re.DOTALL)
print(f'Found {len(tds)} td patterns')
for attr, inner in tds:
    has = 'data-label' in attr
    label = re.search(r'data-label="([^"]+)"', attr)
    print(f'  label={label.group(1) if label else "NONE"} attr={attr[:50]}')

# Also check for data-label in the segment
dl_count = seg.count('data-label=')
print(f'\ndata-label occurrences in renderTable: {dl_count}')