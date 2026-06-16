path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

idx = content.find(b"r.days_left")
print(repr(content[idx:idx+120]))