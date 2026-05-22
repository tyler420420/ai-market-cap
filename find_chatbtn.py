c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
idx=c.find('#chat-btn')
print(repr(c[idx:idx+200]))