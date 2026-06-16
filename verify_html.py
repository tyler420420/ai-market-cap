path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
import re
# Check market cap
mktcaps = re.findall(r'<td data-label="Mkt Cap">([^<]+)</td>', content)
print(f'Mkt cap samples: {mktcaps[:5]}')
# Check mobile CSS
mobile = '@media(max-width:600px)' in content
print(f'Mobile CSS: {mobile}')
# Check JS data-labels in renderTable
idx = content.find('renderTable()')
seg = content[idx:idx+3000]
dl_count = seg.count('data-label=')
print(f'JS data-labels in renderTable: {dl_count}')
# Check TH data-labels
ths = re.findall(r'data-label="([^"]+)"', content[:8000])
print(f'TH data-labels: {ths[:10]}')