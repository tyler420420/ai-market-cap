c=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8').read()
import re
m = re.search(r'"earnings_date":\s*"[^"]+"', c)
if m: print('Data:', m.group(0)[:60])
print('Has earn-cell with br:', 'earn-cell>' in c)