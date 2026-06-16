path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
idx = content.find('html+=&#39;<tr style')
if idx >= 0:
    print(repr(content[idx:idx+400]))
else:
    print('not found at all')
    # check if the entire renderTable section exists
    idx2 = content.find('function renderTable')
    if idx2 >= 0:
        print('renderTable found at', idx2)
        print(repr(content[idx2:idx2+300]))
    else:
        print('renderTable not found')