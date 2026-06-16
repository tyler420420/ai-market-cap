path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Check which columns have data-label
import re
# Find first row
idx = content.find('data-label=')
seg = content[idx:idx+3000]
labels = re.findall(r'data-label="([^"]+)"', seg)
print(f'Found {len(labels)} data-labels in first row section')
for l in labels:
    print(f'  {l}')

# Check for columns MISSING data-label
print('\nChecking for columns without data-label in first row:')
# Find first </td> sequence
row_start = content.find('<tr', idx)
row_end = content.find('</tr>', row_start)
row = content[row_start:row_end]
td_matches = re.findall(r'<td([^>]*)>(.*?)</td>', row, re.DOTALL)
for attr, content_td in td_matches[:5]:
    has_label = 'data-label' in attr
    print(f'  has data-label: {has_label}, attr: {attr[:40]}')