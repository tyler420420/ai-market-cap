path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

# Use bytes directly
replacements = [
    # Ticker - bytes from js_seg_out.txt
    (b"html+='<tr style\\\"background:'+bg+'\\\"><td><strong><a href\\\"https://finance.yahoo.com/quote/'+r.ticker+'\\\" target\\\"_blank\\\" style\\\"color:#66b2ff\\\">'+r.ticker+'</a></strong></td>",
     b"html+='<tr style\\\"background:'+bg+'\\\"><td data-label=\"Ticker\"><strong><a href\\\"https://finance.yahoo.com/quote/'+r.ticker+'\\\" target\\\"_blank\\\" style\\\"color:#66b2ff\\\">'+r.ticker+'</a></strong></td>"),
    # Score
    (b"html+='<td><strong style\\\"color:'+c+'\\\";font-size:1.3em\\\">'+r.score+'</strong></td>",
     b"html+='<td data-label=\"Score\"><strong style\\\"color:'+c+'\\\">'+r.score+'</strong></td>"),
    # Days
    (b"html+='<td style\\\"color:'+(r.days_left==0",
     b"html+='<td data-label=\"Days\" style\\\"color:'+(r.days_left==0"),
    # Strong Buy
    (b"html+='<td style\\\"color:#00ff88\\\">'+r.sb+'</td>",
     b"html+='<td data-label=\"Strong Buy\" style\\\"color:#00ff88\\\">'+r.sb+'</td>"),
    # Buy
    (b"html+='<td style\\\"color:#58a6ff\\\">'+r.buy+'</td>",
     b"html+='<td data-label=\"Buy\" style\\\"color:#58a6ff\\\">'+r.buy+'</td>"),
    # Hold
    (b"html+='<td style\\\"color:#ffcc00\\\">'+r.hold+'</td>",
     b"html+='<td data-label=\"Hold\" style\\\"color:#ffcc00\\\">'+r.hold+'</td>"),
    # Sell
    (b"html+='<td style\\\"color:#ff6b6b\\\">'+r.sell+'</td>",
     b"html+='<td data-label=\"Sell\" style\\\"color:#ff6b6b\\\">'+r.sell+'</td>"),
]

changes = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new, 1)
        changes += 1
        print(f'OK: {old[:40]}')
    else:
        print(f'MISS: {old[:50]}')

print(f'\nTotal: {changes}/{len(replacements)}')

if changes >= 5:
    with open(path, 'wb') as f:
        f.write(content)
    print('Written!')
else:
    print('Not enough')