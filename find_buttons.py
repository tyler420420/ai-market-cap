c = open('ai_earnings_scanner.py', encoding='utf-8').read()
idx = c.find('How It Works')
print(repr(c[idx-100:idx+300]))