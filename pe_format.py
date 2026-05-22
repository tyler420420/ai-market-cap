import re

with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find tbody and fix PE Target column to have price and percent on separate lines
tbody_start = c.find('id="stockTableBody">')
tbody_end = c.find('</tbody>', tbody_start)
tbody = c[tbody_start:tbody_end]

# PE Target pattern: $<number> | +<percent>% (no <br> in td)
# Replace with price on one line, percent on next line
def fix_pe(match):
    return '<td style="font-weight:bold">$' + match.group(1) + '<br><span style="color:#00ff88">+' + match.group(2) + '%</span></td>'

result = re.sub(r'<td>\$(\d+\.?\d*) \| \+(\d+\.?\d*)%</td>', fix_pe, tbody)

if result != tbody:
    c = c[:tbody_start] + result + c[tbody_end:]
    old_count = len(re.findall(r'<td>\$\d+\.?\d* \| \+\d+\.?\d*%</td>', tbody))
    new_count = len(re.findall(r'<td style="font-weight:bold">\$', result))
    print(f'Fixed {new_count} PE Target cells')
    with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'w', encoding='utf-8') as f:
        f.write(c)
else:
    print('Pattern not found')