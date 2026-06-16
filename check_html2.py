path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Check TH pattern
idx = content.find('<th onclick')
if idx >= 0:
    print('TH sample:')
    print(repr(content[idx:idx+200]))
    print()

# Check JS renderTable
idx = content.find('renderTable()')
if idx >= 0:
    seg = content[idx:idx+500]
    print('renderTable sample:')
    print(repr(seg[:300]))
    print()

# Check static rows for data-label
idx = content.find('data-label="Ticker"')
if idx >= 0:
    print('Static Ticker label found!')
else:
    print('NO static Ticker label')
    
# Check what data-label appears in the file
import re
dls = re.findall(r'data-label="([^"]+)"', content)
print(f'Total data-label occurrences: {len(dls)}')
print(f'Sample labels: {dls[:10]}')