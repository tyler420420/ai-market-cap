c = open('ai_earnings_scanner.py', encoding='utf-8').read()
print('Container in source:', '1400px' in c)
idx = c.find('</style></head><body>')
print(repr(c[idx:idx+50]))