c=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8').read()
# look for row background colors
for kw in ['.stock-row','background:#','bg:']:
    idx=c.find(kw)
    while idx>=0:
        snippet=c[idx:idx+100]
        if '#' in snippet[:50]:
            print(repr(snippet[:80]))
            print('---')
        idx=c.find(kw,idx+1)