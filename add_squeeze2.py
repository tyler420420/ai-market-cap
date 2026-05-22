import re

with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add squeeze to getVal map
old1 = "'short_int':r.short_int,'iv':r.iv"
new1 = "'short_int':r.short_int,'iv':r.iv,'squeeze':r.squeeze"
if old1 in c:
    c = c.replace(old1, new1)
    print('Step 1 done: squeeze in getVal')
else:
    print('Step 1 FAILED')

# 2. Add squeeze to sortBy
old2 = "col==='short_int'||col==='iv';}"
new2 = "col==='short_int'||col==='iv'||col==='squeeze';}"
if old2 in c:
    c = c.replace(old2, new2)
    print('Step 2 done: squeeze in sortBy')
else:
    print('Step 2 FAILED')

with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('File saved')