import requests
from bs4 import BeautifulSoup
import re

tickers = []
for page in range(1, 1001, 20):
    url = f'https://finviz.com/screener.ashx?v=152&f=ind_artificial-intelligence&o=ticker&r={page}'
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table', class_='screener_table')
    if not table:
        break
    rows = table.find_all('tr')[1:]
    if not rows:
        break
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 2:
            t = cells[1].get_text(strip=True)
            if t.isalpha() and len(t) <= 5:
                tickers.append(t)
    if len(rows) < 20:
        break
    print(f'page {page}: {len(tickers)} total so far')

print(f'Total AI stocks found: {len(tickers)}')
m = re.search(r'#1 / (\d+) Total', r.text)
print('finviz total:', m.group(1) if m else 'unknown')