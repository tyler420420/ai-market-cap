c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
old = '#chat-btn{position:fixed;bottom:24px;right:24px;background:#238636;color:#fff;border:none;border-radius:8px;padding:12px 24px;font-size:0.95em;font-weight:bold;cursor:pointer;box-shadow:0 4px 20px rgb'
new = '#chat-btn{position:fixed;bottom:24px;right:24px;background:#ffd700;color:#000;border:2px solid #000;border-radius:10px;padding:14px 28px;font-size:1.05em;font-weight:bold;cursor:pointer;box-shadow:0 0 12px rgba(255,215,0,0.5);z-index:9999'
if old in c:
    c=c.replace(old,new)
    open('ai_earnings_scanner.py','w',encoding='utf-8').write(c)
    print('Done')
else:
    print('Not found')
    idx=c.find('#chat-btn{position')
    print(repr(c[idx:idx+200]))