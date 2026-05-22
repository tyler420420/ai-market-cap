c = open('ai_earnings_scanner.py', encoding='utf-8').read()
idx = c.find('class=header')
print(repr(c[idx:idx+300]))