path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the style end line
for i, line in enumerate(lines):
    if '</style></head><body>' in line:
        print(f'Line {i+1}: {repr(line)}')
        # Check the line before
        print(f'Line {i}: {repr(lines[i-1])}')
        break