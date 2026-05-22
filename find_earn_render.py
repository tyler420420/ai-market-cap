c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
idx=c.find("r.earnings_date")
print(repr(c[idx-20:idx+80]))
print()
# Find the renderTable function earnings_date part
import re
for m in re.finditer(r"r\.earnings_date|e\.earnings", c):
    print(m.start(), repr(c[m.start():m.start()+80]))