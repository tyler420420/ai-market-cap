path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find renderTable function
idx = content.find('renderTable()')
seg = content[idx:idx+2000]

# Look for td patterns in JS
import re
tds = re.findall(r"html\+='<td([^>]+)>", seg)
print(f'Found {len(tds)} td patterns in renderTable')
for t in tds[:5]:
    print(f'  {t}')

# Check if any have data-label
has_label = [t for t in tds if 'data-label' in t]
print(f'\nTDs with data-label: {len(has_label)}')
print(f'TDs without data-label: {len(tds) - len(has_label)}')