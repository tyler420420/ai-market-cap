import re
f=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8')
c=f.read()
f.close()
# Fix sell price - find exact pattern
matches = list(re.finditer(r'color:#58a6ff">\$', c))
print(f'Found {len(matches)} matches for sell color')
if matches:
    for m in matches:
        print(f'At {m.start()}: {c[m.start()-30:m.start()+50]}')
# Do the replacement
c=c.replace('color:#58a6ff">$','color:#00ff88">$')
f=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','w',encoding='utf-8')
f.write(c)
f.close()
print('done')
# Verify
f=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8')
c=f.read()
f.close()
idx=c.find('Sell:')
print('Sell:', c[idx-10:idx+60])