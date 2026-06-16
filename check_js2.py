path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('renderTable()')
seg = content[idx:idx+5000]
# Find the rowsData.forEach section
idx2 = seg.find('rowsData.forEach')
if idx2 >= 0:
    chunk = seg[idx2:idx2+3000]
    print(repr(chunk[:500]))
    dl_count = chunk.count('data-label=')
    print(f'\ndata-label in forEach: {dl_count}')
    
# Also check static rows
idx3 = content.find('data-label="Ticker"')
seg2 = content[idx3-10:idx3+200]
print(f'\nStatic Ticker row: {repr(seg2)}')