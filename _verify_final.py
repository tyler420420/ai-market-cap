with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', encoding='utf-8') as f:
    html = f.read()

import re, json

# Check rowsData has fresh data (June 17)
rows_data_match = re.search(r'var rowsData=\[', html)
if rows_data_match:
    start = rows_data_match.start()
    end = html.find('];', start) + 2
    rows_data_str = html[start+len('var rowsData='):end]
    try:
        data = json.loads(rows_data_str)
        print(f'rowsData: {len(data)} stocks')
        print(f'Top 3: {data[0]["ticker"]} ({data[0]["score"]}), {data[1]["ticker"]} ({data[1]["score"]}), {data[2]["ticker"]} ({data[2]["score"]})')
        print(f'First earnings: {data[0]["earnings_date"]} (days_left: {data[0]["days_left"]})')
    except Exception as e:
        print(f'JSON parse error: {e}')
        print(f'Stocks found: {rows_data_str.count("ticker")}')

# Check static rows have fresh data
tbody_start = html.find('<tbody id="stockTableBody">')
tbody_end = html.find('</tbody>')
tbody_content = html[tbody_start:tbody_end]
first_row = tbody_content[tbody_content.find('<tr '):tbody_content.find('</tr>')]
print(f'\nFirst static row contains: {repr(first_row[:200])}')
# Check if it has current data (NOW $95)
print(f'Has NOW: {"NOW" in first_row}')
print(f'Has $95: {"$95" in first_row}')
print(f'Has ServiceNow: {"ServiceNow" in first_row}')

# Verify no broken JS in the sortBy/renderTable
sortby_pos = html.rfind('sortBy(')
print(f'\nsortBy at end of file: {html.rfind("sortBy(", sortby_pos-10) >= sortby_pos - 10}')

print(f'\nTotal file size: {len(html)} bytes')
