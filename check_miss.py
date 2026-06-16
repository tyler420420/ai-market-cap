path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Check the MISS patterns
miss_patterns = [
    "html+='<tr style",
    "html+='<td><strong style",
    "html+='<td style=\"color:'",
    "html+='<td style=\"color:#00ff88\">'+r.sb",
    "html+='<td style=\"color:#58a6ff\">'+r.buy",
    "html+='<td style=\"color:#ffcc00\">'+r.hold",
    "html+='<td style=\"color:#ff6b6b\">'+r.sell",
]

for p in miss_patterns:
    if p in content:
        idx = content.find(p)
        print(f'FOUND: {repr(content[idx:idx+80])}')
    else:
        print(f'NOT FOUND: {p[:50]}')