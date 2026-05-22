with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix the mixed quote issue on the hold line
old = """html+="<td style="color:#58a6ff">'+r.buy+'</td>';html+='<td style="color:#ffcc00">'+r.hold+'</td>\""""
new = """html+='<td style="color:#58a6ff">'+r.buy+'</td>';html+='<td style="color:#ffcc00">'+r.hold+'</td>'"""

print('Old in file:', old in c)
print('Checking for mixed quotes...')
# Find the problematic area
idx = c.find('color:#ffcc00">')
if idx >= 0:
    print('Context around #ffcc00>:', repr(c[idx-20:idx+50]))
    
# Try replacing just the broken part
bad = "html+=''<td style=\"color:#ffcc00\">'+r.hold+'</td>'"
if bad in c:
    print('Found bad hold line')
    
# Actually let's just find all variations of this pattern
import re
matches = list(re.finditer(r"html\+\='<td[^']*r\.(buy|hold)", c))
for m in matches:
    print(f'At {m.start()}: {repr(m.group())}')