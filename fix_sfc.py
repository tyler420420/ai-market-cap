c=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8').read()
# Fix the chr(10) in JS to be String.fromCharCode(10) so the replace works
c=c.replace(
    "r.earnings_date.replace(chr(10),'<br>')",
    "r.earnings_date.replace(String.fromCharCode(10),'<br>')"
)
open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','w',encoding='utf-8').write(c)
import shutil
shutil.copy('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','C:\\Users\\Tyler_AI\\Desktop\\AI_Market_Cap_Scanner_v2.html')
print('Done')
# Verify
import re
m = re.search(r'fromCharCode.*earn', c)
print('Fixed:' , m.group(0) if m else 'none')