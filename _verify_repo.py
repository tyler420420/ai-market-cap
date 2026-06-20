import json, re
with open('scanner.html', encoding='utf-8') as f:
    html = f.read()
rows_match = re.search(r'var rowsData=(\[\{.*?\}\]);', html, re.DOTALL)
data = json.loads(rows_match.group(1))
print(f'Scanner.html: {len(data)} stocks')
print(f'Top 3: {data[0]["ticker"]} ({data[0]["score"]}), {data[1]["ticker"]} ({data[1]["score"]}), {data[2]["ticker"]} ({data[2]["score"]})')
static_rows = html.count('<tr ')
print(f'Static rows: {static_rows}')
print(f'File size: {len(html)} bytes')
