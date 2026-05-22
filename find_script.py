c = open('ai_earnings_scanner.py', encoding='utf-8').read()
idx = c.find('rowsData=')
print(repr(c[idx-50:idx+50]))