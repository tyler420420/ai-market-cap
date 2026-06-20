import json, re

with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', encoding='utf-8') as f:
    html = f.read()

# Find the rowsData JSON - it's after 'var rowsData='
# Use a proper JSON-aware parse to find the array boundaries
rows_match = re.search(r'var rowsData=(\[\{.*?\}\]);', html, re.DOTALL)
if rows_match:
    rows_str = rows_match.group(1)
    print(f'rowsData match: {len(rows_str)} chars')
    try:
        data = json.loads(rows_str)
        print(f'Parsed: {len(data)} stocks')
        print(f'Top 3: {data[0]["ticker"]} ({data[0]["score"]}), {data[1]["ticker"]} ({data[1]["score"]}), {data[2]["ticker"]} ({data[2]["score"]})')
    except Exception as e:
        print(f'Error: {e}')
        print(f'First 200 chars: {rows_str[:200]}')
        print(f'Last 200 chars: {rows_str[-200:]}')
else:
    print('No rowsData match found')
    # Find var rowsData= position
    pos = html.find('var rowsData=')
    print(f'var rowsData= at: {pos}')
    print(f'Context: {repr(html[pos:pos+100])}')
