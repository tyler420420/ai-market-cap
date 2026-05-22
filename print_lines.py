with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and print lines 527-532
for i in range(526, 533):
    print(f'Line {i+1}: {repr(lines[i][:100])}')