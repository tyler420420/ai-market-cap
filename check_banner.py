c=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8').read()
import re
m = re.search(r'pick-banner\{([^}]+)\}', c)
if m:
    print('EXACT:', repr(m.group(0)))