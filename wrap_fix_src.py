c = open('ai_earnings_scanner.py', encoding='utf-8').read()

old = "html += '<body>'"
new = "html += '<body><div style=\"max-width:1400px;margin:0 auto\">'"

old2 = "html += '</body>'"
new2 = "html += '</div></body>'"

if old in c:
    c = c.replace(old, new)
    c = c.replace(old2, new2)
    open('ai_earnings_scanner.py', 'w', encoding='utf-8').write(c)
    print('Source updated')
else:
    print('NOT found')