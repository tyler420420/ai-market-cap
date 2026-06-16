path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'rb') as f:
    content = f.read()
# Find the first static row days cell
idx = content.find(b"data-label=\"Days\"")
if idx >= 0:
    print(repr(content[idx:idx+100]))
else:
    print("Not found")
    # Try another way
    idx = content.find(b"Days Left")
    if idx >= 0:
        print(repr(content[idx:idx+100]))