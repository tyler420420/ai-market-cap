import urllib.request, re
req = urllib.request.Request('https://aismarketcap.com/', headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=15)
html = resp.read().decode()

# Check the stock table body
idx = html.find('<tbody')
end = html.find('</tbody>', idx)
tbody = html[idx:end+8]
print('TBODY:', tbody[:200])
print()

# Check rowsData
m = re.search(r'var rowsData\s*=\s*(\[.*?\]);', html, re.DOTALL)
if m:
    data = m.group(1)
    print('rowsData:', data[:300])
    print('rowsData length:', len(data))
else:
    print('No rowsData match')

# Check if ai_earnings_today exists
print()
print('Serving ai_earnings_today:', 'ai_earnings_today' in html)
dated = re.findall(r'ai_earnings_(\d+_\d+)\.html', html)
print('Dated files:', dated[:3])

# Count rows
rows = len(re.findall(r'<tr class="stock-row', html))
print('Stock rows in HTML:', rows)

# Check for any content in tbody
has_data = '<td>' in tbody and 'NVDA' in html
print('Has real stock data:', has_data)