import re, json
from pathlib import Path

test = Path(r'C:\Users\Tyler_AI\Desktop\test_scanner.html')
html = test.read_text(encoding='utf-8')

# Get tbody rows specifically
tbody_match = re.search(r'<tbody[^>]*id="stockTableBody"[^>]*>(.*?)</tbody>', html, re.DOTALL)
if not tbody_match:
    print('No tbody found!')
    exit()

tbody = tbody_match.group(1)
rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody, re.DOTALL)
print('Table rows in tbody:', len(rows))

for i, row in enumerate(rows[:5]):
    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
    print(f'\nRow {i+1} ({len(cells)} cells):')
    if cells:
        ticker_m = re.search(r'>([A-Z]{1,5})</a>', cells[0])
        ticker = ticker_m.group(1) if ticker_m else '?'
        # Clean cells of HTML
        clean = [re.sub(r'<[^>]+>', '', c).strip()[:30] for c in cells]
        print(f'  Ticker: {ticker}')
        print(f'  Cols: {clean}')
    else:
        print('  No cells!')

# Check what JS renderTable does
print('\n--- Checking renderTable ---')
render_match = re.search(r'function renderTable\(\)(.*?)function ', html, re.DOTALL)
if render_match:
    print('renderTable found, first 300 chars:')
    print(render_match.group(1)[:300])
