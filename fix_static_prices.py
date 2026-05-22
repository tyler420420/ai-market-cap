with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix static HTML tbody prices - they're not bold yet
# Price pattern: <td>$NUMBER</td> - need to make it <td style="font-weight:bold">$NUMBER</td>
# But only the Price column (5th column in each row), not other dollar amounts like PE Target, 3D, 5D

import re

# Strategy: each row starts with a <tr> in tbody, find the 5th <td> (price column) and make it bold
# Pattern: after days_left column (has style) comes the price column as plain <td>$PRICE</td>

# Find tbody section
tbody_start = c.find('id="stockTableBody">')
tbody_end = c.find('</tbody>', tbody_start)
tbody = c[tbody_start:tbody_end]

# Count rows and fix price TDs
# Price column is the 6th <td> (index 5) in each row, comes right after the days_left td which has style
# Pattern: the price td has NO style attribute and starts with $ followed by a number

# Replace price td (plain <td>$ followed by number, no style) with bold version
# But be careful - PE Target also starts with $ but has | in the same td

# The price column is specifically the td that is just $<number with no other content
# It comes after the days_left td (which has style="color:...")

# Better approach: in the tbody, find all <td>$ patterns and identify which are price vs PE/3D/5D
# Price column: just $<number without |
# PE/3D/5D columns: $<number | +...%

def make_price_bold(match):
    return '<td style="font-weight:bold">' + match.group(1) + '</td>'

# Pattern for price td: <td>$ followed by number, ending with </td> (no | in it)
# This regex matches <td>$NUMBER</td> where NUMBER is decimal
result = re.sub(r'<td>(\$\d+\.?\d*)</td>', make_price_bold, tbody)

if result != tbody:
    c = c[:tbody_start] + result + c[tbody_end:]
    with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'w', encoding='utf-8') as f:
        f.write(c)
    # count changes
    old_count = len(re.findall(r'<td>(\$\d+\.?\d*)</td>', tbody))
    new_count = len(re.findall(r'<td style="font-weight:bold">(\$\d+\.?\d*)</td>', result))
    print(f'Fixed {new_count} price cells bold')
else:
    print('No prices found to fix')