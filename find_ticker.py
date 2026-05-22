content = open('ai_earnings_scanner.py', encoding='utf-8').read()
idx = content.find("class=ticker-strip")
print('ticker-strip found:', idx >= 0)
if idx >= 0:
    print(repr(content[idx-100:idx+200]))