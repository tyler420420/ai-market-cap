content = open('ai_earnings_scanner.py', encoding='utf-8').read()
# Find the ticker-strip line
idx = content.find("class=ticker-strip")
print('Found at:', idx)
if idx >= 0:
    print(repr(content[idx-50:idx+500]))