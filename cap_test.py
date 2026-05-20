import requests, time
from bs4 import BeautifulSoup
import re

# Test: cap_large + cap_mega should cover 10B+
tests = [
    ('sec_technology,cap_large', 'sec_technology,cap_large'),
    ('cap_large+cap_mega', 'sec_technology,cap_large,cap_mega'),
    ('cap_mega only', 'sec_technology,cap_mega'),
]

for name, f in tests:
    time.sleep(2)
    url = f'https://finviz.com/screener.ashx?v=152&f={f}&o=ticker&r=1'
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table', class_='screener_table')
    rows = len(table.find_all('tr')) - 1 if table else 0
    m = re.search(r'#1 / (\d+) Total', r.text)
    total = m.group(1) if m else '?'
    print(f'{name}: total={total}, page1={rows}')
    if rows > 0 and table:
        cells = table.find_all('tr')[1].find_all('td')
        if len(cells) >= 7:
            print(f'  First: {cells[1].get_text(strip=True)} {cells[6].get_text(strip=True)}')