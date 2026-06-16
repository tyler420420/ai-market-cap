path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Read the actual segment from the file
with open(r'C:\Users\Tyler_AI\ai-market-cap\js_seg_out.txt', 'r', encoding='utf-8') as f:
    actual_seg = f.read()

print('Actual segment first 50 chars:', repr(actual_seg[:50]))

# Build replacements using the actual text from js_seg_out.txt
# The file has \" for escaped double quotes
replacements = [
    # Ticker
    ("html+='<tr style\\\"background:'+bg+'\\\"><td><strong><a href\\\"https://finance.yahoo.com/quote/'+r.ticker+'\\\" target\\\"_blank\\\" style\\\"color:#66b2ff\\\">'+r.ticker+'</a></strong></td>",
     "html+='<tr style\\\"background:'+bg+'\\\"><td data-label=\"Ticker\"><strong><a href\\\"https://finance.yahoo.com/quote/'+r.ticker+'\\\" target\\\"_blank\\\" style\\\"color:#66b2ff\\\">'+r.ticker+'</a></strong></td>"),
    # Score
    ("html+='<td><strong style\\\"color:'+c+'\\\";font-size:1.3em\\\">'+r.score+'</strong></td>",
     "html+='<td data-label=\"Score\"><strong style\\\"color:'+c+'\\\">'+r.score+'</strong></td>"),
    # Days
    ("html+='<td style\\\"color:'+(r.days_left==0",
     "html+='<td data-label=\"Days\" style\\\"color:'+(r.days_left==0"),
    # Strong Buy
    ("html+='<td style\\\"color:#00ff88\\\">'+r.sb+'</td>",
     "html+='<td data-label=\"Strong Buy\" style\\\"color:#00ff88\\\">'+r.sb+'</td>"),
    # Buy
    ("html+='<td style\\\"color:#58a6ff\\\">'+r.buy+'</td>",
     "html+='<td data-label=\"Buy\" style\\\"color:#58a6ff\\\">'+r.buy+'</td>"),
    # Hold
    ("html+='<td style\\\"color:#ffcc00\\\">'+r.hold+'</td>",
     "html+='<td data-label=\"Hold\" style\\\"color:#ffcc00\\\">'+r.hold+'</td>"),
    # Sell
    ("html+='<td style\\\"color:#ff6b6b\\\">'+r.sell+'</td>",
     "html+='<td data-label=\"Sell\" style\\\"color:#ff6b6b\\\">'+r.sell+'</td>"),
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