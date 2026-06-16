path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

# Exact bytes from dump:
# html+='<td style=\"color:'+(r.days_left==0?'#ff4444':(r.days_left<=7?'#00ff88':'#ffcc00'))+';font-weight:bold\">'+(r.days_left==0?'Today':r.days_left+'d')+'</td>'
old = b"html+='<td style=\\\"color:\\'+(r.days_left==0?\\'#ff4444\\':(r.days_left<=7?\\'#00ff88\\':\\'#ffcc00\\'))+\\\";font-weight:bold\\\">\\'+(r.days_left==0?\\'Today\\':r.days_left+\\'d\\')+\\'</td>"
new = b"html+='<td style=\\\"color:\\'+(r.days_left==0?\\'#ff4444\\':(r.days_left<=14?\\'#ffcc00\\':(r.days_left<=35?\\'#58a6ff\\':\\'#00ff88\\'))+\\\";font-weight:bold\\\">\\'+(r.days_left==0?\\'Today\\':r.days_left+\\'d\\')+\\'</td>"

print(f"Old len: {len(old)}, New len: {len(new)}")
print(f"Old hex: {old.hex()}")
print()

# Find in content
idx = content.find(old)
if idx >= 0:
    content = content.replace(old, new)
    with open(path, 'wb') as f:
        f.write(content)
    print('OK - replaced')
else:
    print('MISS')
    # find the actual start
    idx2 = content.find(b"html+='<td style")
    if idx2 >= 0:
        chunk = content[idx2:idx2+len(old)+10]
        print(f"Actual hex: {chunk.hex()}")
        print(f"Actual: {repr(chunk)}")