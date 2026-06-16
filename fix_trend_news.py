path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

# Find the trend segment and replace
old = b"html+='<td>'+(r.squeeze?'<span style=\\'background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88\\'>Yes</span>':'\xc3\xa2\xe2\x82\xac\xe2\x80\x9d')+'</td>"
new = b"html+='<td data-label=\"Trend\">+(r.squeeze?'<span style=\\'background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88\\'>Yes</span>':'\xc3\xa2\xe2\x82\xac\xe2\x80\x9d')+'</td>"

if old in content:
    content = content.replace(old, new, 1)
    print('OK: trend')
else:
    print('MISS: trend')

# Also do news
old2 = b"html+='<td>'+newsHtml(r.news)+'</td></tr>'"
new2 = b"html+='<td data-label=\"News\">'+newsHtml(r.news)+'</td></tr>'"
if old2 in content:
    content = content.replace(old2, new2, 1)
    print('OK: news')
else:
    print('MISS: news')

with open(path, 'wb') as f:
    f.write(content)
print('Written!')