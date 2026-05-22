c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
import re
for m in re.finditer(r'strftime|earnings_date|edate', c):
    print(m.start(), repr(c[m.start():m.start()+60]))
    print('---')