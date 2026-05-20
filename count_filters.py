import requests
from bs4 import BeautifulSoup
import re

tests = [
    'sec_technology,cap_small',
    'sec_technology,cap_mid',
    'sec_technology,cap_large',
    'sec_technology,cap_micro',
    'sec_technology,cap_small,cap_mid,cap_large',
]

for f in tests:
    url = f'https://finviz.com/screener.ashx?v=152&f={f}&o=ticker&r=1'
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
    m = re.search(r'#1 / (\d+) Total', r.text)
    total = m.group(1) if m else '?'
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table', class_='screener_table')
    rows = len(table.find_all('tr')) - 1 if table else 0
    print(f'{f}: total={total}, page1={rows}')