c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
# The <br> inside the JS string is being parsed as a Python br tag
# We need to escape it or use String.fromCharCode
# Check what fmtEdate looks like right now
import re
m = re.search(r'fmtEdate\(s\).*?return[^;]+;', c)
if m: print(repr(m.group(0)))
else:
    idx=c.find('fmtEdate')
    print(repr(c[idx:idx+200]))