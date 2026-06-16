path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Use raw strings to avoid escaping issues
replacements = [
    # Ticker - in file: html+='<tr style\"background:'+bg+'\"><td><strong>
    (r"html+='<tr style\\\"background:'+bg+'\\\"><td><strong><a href\\\"https://finance.yahoo.com/quote/'+r.ticker+'\\\" target\\\"_blank\\\" style\\\"color:#66b2ff\\\">'+r.ticker+'</a></strong></td>",
     r"html+='<tr style\\\"background:'+bg+'\\\"><td data-label=\"Ticker\"><strong><a href\\\"https://finance.yahoo.com/quote/'+r.ticker+'\\\" target\\\"_blank\\\" style\\\"color:#66b2ff\\\">'+r.ticker+'</a></strong></td>"),
    # Score
    (r"html+='<td><strong style\\\"color:'+c+'\\\";font-size:1.3em\\\">'+r.score+'</strong></td>",
     r"html+='<td data-label=\"Score\"><strong style\\\"color:'+c+'\\\">'+r.score+'</strong></td>"),
    # Days
    (r"html+='<td style\\\"color:'+(r.days_left==0",
     r"html+='<td data-label=\"Days\" style\\\"color:'+(r.days_left==0"),
    # Strong Buy
    (r"html+='<td style\\\"color:#00ff88\\\">'+r.sb+'</td>",
     r"html+='<td data-label=\"Strong Buy\" style\\\"color:#00ff88\\\">'+r.sb+'</td>"),
    # Buy
    (r"html+='<td style\\\"color:#58a6ff\\\">'+r.buy+'</td>",
     r"html+='<td data-label=\"Buy\" style\\\"color:#58a6ff\\\">'+r.buy+'</td>"),
    # Hold
    (r"html+='<td style\\\"color:#ffcc00\\\">'+r.hold+'</td>",
     r"html+='<td data-label=\"Hold\" style\\\"color:#ffcc00\\\">'+r.hold+'</td>"),
    # Sell
    (r"html+='<td style\\\"color:#ff6b6b\\\">'+r.sell+'</td>",
     r"html+='<td data-label=\"Sell\" style\\\"color:#ff6b6b\\\">'+r.sell+'</td>"),
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
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Written!')
else:
    print('Not enough')