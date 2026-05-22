content = open('ai_earnings_scanner.py', encoding='utf-8').read()
# Find SCANNER_TITLE usage
idx = content.find("SCANNER_TITLE")
print('SCANNER_TITLE at:', idx)
if idx >= 0:
    print(repr(content[idx-50:idx+150]))