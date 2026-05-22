c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
import re
# Find the renderTable function and earnings_date cell
m = re.search(r"function renderTable\(\)\{.*?forEach.*?html\+=.*?earnings_date.*?\}", c, re.DOTALL)
if m:
    print(repr(m.group(0)[:500]))
else:
    # Look for the cell building
    idx=c.find("'<td>'+r.earnings_date")
    print('earnings_date cell at:', idx)
    if idx>0:
        print(repr(c[idx-100:idx+200]))