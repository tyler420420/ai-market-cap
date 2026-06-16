path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find("html+='<tr style=\"background:'+bg+'\"")
if idx >= 0:
    print('FOUND with background:')
    print(repr(content[idx:idx+800]))
else:
    print('not found')
    idx = content.find("html+= '<tr style=\"background:'")
    print('searching for html+=...')
    idx2 = content.find('html+=')
    if idx2 >= 0:
        print('html+= found at', idx2)
        print(repr(content[idx2:idx2+100]))