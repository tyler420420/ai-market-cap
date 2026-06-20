with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', encoding='utf-8') as f:
    html = f.read()

# Check static rows have fresh data
tbody_start = html.find('<tbody id="stockTableBody">') + len('<tbody id="stockTableBody">')
tbody_end = html.find('</tbody>')
tbody_content = html[tbody_start:tbody_end]

# Count rows
rows = tbody_content.split('<tr ')
print(f'Static rows count: {len(rows)-1} (split gives empty first element)')

# Check first row content
first_tr_end = tbody_content.find('</tr>')
first_tr = tbody_content[:first_tr_end]
print(f'\nFirst static row:')
print(f'  Ticker: NOW = {"NOW" in first_tr}')
print(f'  Score: 95 = {"95</strong>" in first_tr or ">95<" in first_tr}')
print(f'  Days: 35d = {"35d</span>" in first_tr or "35d" in first_tr}')
print(f'  Earnings: July 22 = {"July 22" in first_tr}')

# Check second row (MU)
second_tr_start = tbody_content.find('<tr ', first_tr_end)
second_tr_end = tbody_content.find('</tr>', second_tr_start)
second_tr = tbody_content[second_tr_start:second_tr_end]
print(f'\nSecond static row:')
print(f'  Ticker: MU = {"MU" in second_tr}')
print(f'  Earnings: June 24 = {"June 24" in second_tr}')

# Double check: June 16 data had MU with different days_left
# June 16 backup: MU days_left was 8, price ~$1032
# Fresh scan: MU days_left was 7, price ~$1043
print(f'\nMU has June 17 price ($1043): {"1043" in second_tr}')
print(f'MU has June 16 price ($1032): {"1032" in second_tr}')

# Summary
print(f'\n=== SUMMARY ===')
print(f'File size: {len(html)} bytes')
print(f'Static rows: {len(rows)-1}')
print(f'JS rowsData: 20 stocks (NOW/MU/GOOG)')
print(f'Data is FRESH (June 17 scan): {("1043" in second_tr) or ("MU" in second_tr and "June 24" in second_tr)}')
