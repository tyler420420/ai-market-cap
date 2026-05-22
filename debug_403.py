f=open('scanner_web.py','r',encoding='utf-8')
c=f.read()
f.close()
# Find all route decorators and before_request
import re
routes = re.findall(r'(@app\.route.*?)\ndef ', c)
print('ROUTES:')
for r in routes:
    print(r)
print()
before = re.findall(r'(@app\.before.*?)\ndef ', c)
print('BEFORE REQUESTS:')
for b in before:
    print(b)
print()
# Check if there's a 403 return anywhere
idx = c.find('403')
while idx >= 0:
    print(f'403 at {idx}:', c[max(0,idx-50):idx+100])
    print('---')
    idx = c.find('403', idx+1)