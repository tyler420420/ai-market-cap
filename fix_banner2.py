c=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8').read()
# Check exact bytes of the pick-banner line
import re
m = re.search(r'pick-banner\{([^}]+)\}', c)
if m:
    print('EXACT:', repr(m.group(0)))
    print('LENGTH:', len(m.group(0)))
    # Try to replace just the gradient part
    old = 'background:linear-gradient(135deg,#2a1a00,#ffd700)'
    new = 'background:#ffd700'
    if old in c:
        print('FOUND old gradient')
        c=c.replace(old,new)
        open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','w',encoding='utf-8').write(c)
        import shutil
        shutil.copy('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','C:\\Users\\Tyler_AI\\Desktop\\AI_Market_Cap_Scanner_v2.html')
        print('Done')
    else:
        print('old not found')
        # check what's there
        print(repr(m.group(1)[:100]))
else:
    print('no match')