c = open('ai_earnings_scanner.py', encoding='utf-8').read()
old = "html += '</style></head><body><div style=\"max-width:1400px;margin:0 auto\">'"
new = "html += '</style></head><body>'"
if old in c:
    c = c.replace(old, new)
    open('ai_earnings_scanner.py', 'w', encoding='utf-8').write(c)
    print('Container removed from source')
else:
    print('NOT found')
    # Try to find what it looks like
    idx = c.find("'</style></head><body>")
    print(repr(c[idx:idx+80]))