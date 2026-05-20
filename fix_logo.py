with open('index.html','r',encoding='utf-8',errors='replace') as f: c=f.read()
old = '<img src="AI_Market_Cap_Logo3.png" alt="AI Market Cap" style="height:34px;border-radius:6px;"><span style="font-size:1em;font-weight:bold;color:#58a6ff;letter-spacing:-0.5px;">AI Market Cap</span>'
new = '<span style="font-size:1.1em;font-weight:bold;color:#58a6ff;">AI Market Cap</span>'
if old in c:
    c=c.replace(old,new)
    open('index.html','w',encoding='utf-8',newline='').write(c)
    print('Done')
else:
    print('Not found')
