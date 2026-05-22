f=open('scanner_web.py','r',encoding='utf-8')
c=f.read()
f.close()
idx=c.find('return 403')
if idx>0:
    print(c[max(0,idx-200):idx+200])
print('===')
# Find the function that does 403 return
idx=c.find("abort(403")
if idx>0:
    print(c[max(0,idx-300):idx+200])
print('===')
# Check all aborts
import re
aborts = [(m.start(), c[max(0,m.start()-100):m.start()+50]) for m in re.finditer(r'abort\(403\)', c)]
for pos, ctx in aborts:
    print(f'abort at {pos}:')
    print(ctx)
    print('---')