content = open('ai_earnings_scanner.py').read()
# Find the score rendering in renderTable JS
idx = content.find('style.color')
print('style.color found at:', idx)
if idx >= 0:
    print(repr(content[idx-30:idx+80]))