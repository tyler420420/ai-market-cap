path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find("html+='<tr style")
end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
segment = content[start:end]

# The file uses \" and \' for escaped quotes in the Python string
# Build replacements with correct escaping
replacements = [
    # Ticker
    ('<tr style=\\"background:\\'+bg+\'\\"><td><strong><a href=\\"https://finance.yahoo.com/quote/\\'+r.ticker+\'\\" target=\\"_blank\\" style=\\"color:#66b2ff\\">\\'+r.ticker+\'</a></strong></td>\\';',
     '<tr style=\\"background:\\'+bg+\'\\"><td data-label=\\"Ticker\\"><strong><a href=\\"https://finance.yahoo.com/quote/\\'+r.ticker+\'\\" target=\\"_blank\\" style=\\"color:#66b2ff\\">\\'+r.ticker+\'</a></strong></td>\\';'),
    # Company
    ("html+='<td>\\'+r.company_name.substring(0,35)+(r.company_name.length>35?'...':'')+\\'</td>\\';",
     "html+='<td data-label=\\"Company\\">\\'+r.company_name.substring(0,35)+(r.company_name.length>35?'...':'')+\\'</td>\\';"),
    # Score
    ("html+='<td><strong style=\\"color:\\'+c+';font-size:1.3em\\">\\'+r.score+\\'</strong></td>\\';",
     "html+='<td data-label=\\"Score\\"><strong style=\\"color:\\'+c+\\'\\">\\'+r.score+\\'</strong></td>\\';"),
    # Earnings
    ("html+='<td class=earn-cell>\\'+r.earnings_date.replace(chr(10),'<br>')+\\'</td>\\';",
     "html+='<td data-label=\\"Earnings\\" class=earn-cell>\\'+r.earnings_date.replace(chr(10),'<br>')+\\'</td>\\';"),
    # Days
    ("html+='<td style=\\"color:\\'+(r.days_left==0?'#ff4444':(r.days_left<=7?'#00ff88':'#ffcc00'))+';font-weight:bold\\">\\'+(r.days_left==0?'Today':r.days_left+'d')+\\'</td>\\';",
     "html+='<td data-label=\\"Days\\" style=\\"color:\\'+(r.days_left==0?'#ff4444':(r.days_left<=7?'#00ff88':'#ffcc00'))+';font-weight:bold\\">\\'+(r.days_left==0?'Today':r.days_left+'d')+\\'</td>\\';"),
    # Analysts
    ("html+='<td>\\'+r.analysts+\\'</td>\\';",
     "html+='<td data-label=\\"Analysts\\">\\'+r.analysts+\\'</td>\\';"),
    # Strong Buy
    ("html+='<td style=\\"color:#00ff88\\">\\'+r.sb+\\'</td>\\';",
     "html+='<td data-label=\\"Strong Buy\\" style=\\"color:#00ff88\\">\\'+r.sb+\\'</td>\\';"),
    # Buy
    ("html+='<td style=\\"color:#58a6ff\\">\\'+r.buy+\\'</td>\\';",
     "html+='<td data-label=\\"Buy\\" style=\\"color:#58a6ff\\">\\'+r.buy+\\'</td>\\';"),
    # Hold
    ("html+='<td style=\\"color:#ffcc00\\">\\'+r.hold+\\'</td>\\';",
     "html+='<td data-label=\\"Hold\\" style=\\"color:#ffcc00\\">\\'+r.hold+\\'</td>\\';"),
    # Sell
    ("html+='<td style=\\"color:#ff6b6b\\">\\'+r.sell+\\'</td>\\';",
     "html+='<td data-label=\\"Sell\\" style=\\"color:#ff6b6b\\">\\'+r.sell+\\'</td>\\';"),
    # Mkt Cap
    ("html+='<td>\\'+fmtMktcap(r.mktcap)+\\'</td>\\';",
     "html+='<td data-label=\\"Mkt Cap\\">\\'+fmtMktcap(r.mktcap)+\\'</td>\\';"),
    # Shorts (uses \' in file)
    ("html+='<td style=\\'color:#fff\\'>\\'+r.short_int+'%</td>\\';",
     "html+='<td data-label=\\'Shorts\\' style=\\'color:#fff\\'>\\'+r.short_int+'%</td>\\';"),
    # IV (uses \' in file)
    ("html+='<td style=\\'color:#fff\\'>\\'+r.iv+'%</td>\\';",
     "html+='<td data-label=\\'IV\\' style=\\'color:#fff\\'>\\'+r.iv+'%</td>\\';"),
    # Trend/Squeeze
    ("html+='<td>\\'+(r.squeeze?",
     "html+='<td data-label=\\"Trend\\">\\'+(r.squeeze?"),
    # News
    ("html+='<td>\\'+newsHtml(r.news)+\\'</td></tr>\\';",
     "html+='<td data-label=\\"News\\">\\'+newsHtml(r.news)+\\'</td></tr>\\';"),
]

changes = 0
for old, new in replacements:
    if old in segment:
        segment = segment.replace(old, new, 1)
        changes += 1
        print(f'OK: {old[:50]}')
    else:
        print(f'MISS: {old[:60]}')

print(f'\nTotal: {changes}/16')
if changes >= 14:
    content = content[:start] + segment + content[end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Written!')
else:
    print('Not enough - check MISSes above')