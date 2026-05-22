c=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8').read()
for kw in ['#00ff88','#2ea043','#238636','rgb(0,255']:
    idx=c.find(kw)
    if idx>=0: print(kw,':',repr(c[idx-20:idx+40]))