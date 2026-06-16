path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'rb') as f:
    content = f.read()
idx = content.find(b"days_left")
print(repr(content[idx:idx+120]))