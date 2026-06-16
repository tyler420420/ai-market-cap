path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

# Search for the days color in JS
patterns = [
    b"days_left==0",
    b"days_left<=7",
    b"days_left<=15",
    b"#ff4444",
    b"#ffcc00",
    b"#58a6ff",
]

for p in patterns:
    idx = content.find(p)
    if idx >= 0:
        print(f"Found: {p}")
        print(repr(content[max(0,idx-30):idx+80]))
        print()