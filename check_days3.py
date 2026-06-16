path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'rb') as f:
    content = f.read()
# Find the JS days color logic
idx = content.find(b"r.days_left==0")
if idx >= 0:
    print(repr(content[idx:idx+150]))
else:
    print("Not found")
    idx = content.find(b"renderTable")
    print(repr(content[idx:idx+300]))