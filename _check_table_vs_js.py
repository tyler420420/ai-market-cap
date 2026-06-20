import re, json
from pathlib import Path

test = Path(r'C:\Users\Tyler_AI\Desktop\test_scanner.html')
html = test.read_text(encoding='utf-8')

# Get first 5 rows from the TABLE in the HTML (not just the JS rowsData)
# The table has td cells
tds = re.findall(r'<td[^>]*>(.*?)</td>', html)
print('Total td cells:', len(tds))

# Each row has 18 tds (18 columns)
# Print first 3 complete rows
num_cols = 18
for row_i in range(3):
    print(f'\n--- Row {row_i+1} ---')
    for col_i in range(num_cols):
        idx = row_i * num_cols + col_i
        if idx < len(tds):
            # Clean HTML from cell content
            cell = re.sub(r'<[^>]+>', '', tds[idx]).strip()
            print(f'  Col {col_i}: {cell[:60]}')

# Now check the JS rowsData
idx = html.find('var rowsData=')
arr_depth, end = 0, idx
for i in range(idx + 13, len(html)):
    if html[i] == '[': arr_depth += 1
    elif html[i] == ']':
        arr_depth -= 1
        if arr_depth == 0:
            end = i
            break
rows = json.loads(html[idx + 13:end + 1])
print(f'\n--- rowsData JS ({len(rows)} stocks) ---')
for i, s in enumerate(rows[:3]):
    print(f'  {i+1}. {s["ticker"]}: ${s["price"]}, {s["days_left"]}d, score={s["score"]}')
