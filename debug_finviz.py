import requests, time
from bs4 import BeautifulSoup
import re

for name, f in [('cap_large (10B+)', 'sec_technology,cap_large'), ('cap_mid (2B-10B)', 'sec_technology,cap_mid')]:
    time.sleep(3)
    url = f'https://finviz.com/screener.ashx?v=152&f={f}&o=ticker&r=1'
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
    print(name + ': status=' + str(r.status_code))
    m = re.search(r'#\d+ / (\d+) Total', r.text)
    print('  Total match:', m.group() if m else 'none')
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table', class_='screener_table')
    if table:
        rows = table.find_all('tr')
        print('  Table rows:', len(rows))
        if len(rows) > 1:
            cells = rows[1].find_all('td')
            print('  First row:', [c.get_text(strip=True) for c in cells[:3]])
    else:
        print('  No table. First 500 chars of body:')
        idx = r.text.find('<body')
        print(r.text[idx:idx+500])