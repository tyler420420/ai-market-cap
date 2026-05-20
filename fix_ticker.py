with open('ai_earnings_scanner.py','r',encoding='utf-8',errors='replace') as f: c=f.read()
old = '<span class=ticker-item><span class=ticker-sym>{s.ticker}</span> <span class=ticker-price>'
new = '<span class=ticker-item><span style=\"font-weight:bold;color:#00ff88\">{int(s.composite_score)}</span> <span class=ticker-sym>{s.ticker}</span> <span class=ticker-price>'
if old in c:
    c=c.replace(old,new)
    open('ai_earnings_scanner.py','w',encoding='utf-8',newline='').write(c)
    print('Done - score added to ticker')
else:
    print('Not found')
