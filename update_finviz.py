import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the function start and end
start = end = -1
for i, l in enumerate(lines):
    if 'def fetch_ai_stocks_from_finviz' in l:
        start = i
    if start >= 0 and 'return AI_TICKERS' in l:
        end = i
        break

print(f'Function found at lines {start+1}-{end+1}')

new_func = '''def fetch_ai_stocks_from_finviz() -> List[str]:
    """Fetch AI/artificial-intelligence-tagged stocks from finviz. All pages, no hard cap."""
    try:
        import requests
        from bs4 import BeautifulSoup
        tickers = set()
        for page_start in range(1, 1001, 20):
            url = f"https://finviz.com/screener.ashx?v=152&f=ind_artificial-intelligence&o=ticker&r={page_start}"
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
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
                    if t.isalpha() and 1 <= len(t) <= 5:
                        tickers.add(t)
            if len(rows) < 20:
                break
        result = sorted(tickers)
        print(f"[AI Stocks] Fetched {len(result)} AI stocks from finviz")
        return result
    except Exception as e:
        print(f"[AI Stocks] Finviz fetch failed: {e}. Using cached list.")
        return AI_TICKERS
'''

new_lines = lines[:start] + [new_func] + lines[end+1:]
with open('ai_earnings_scanner.py', 'w', encoding='utf-8', newline='') as f:
    f.writelines(new_lines)
print(f'Written {len(new_lines)} lines')