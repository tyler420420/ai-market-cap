with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

count = 0
for i, line in enumerate(lines):
    if 'buy_rating_pct' in line or ('buy_rating' in line and 'blue' in line):
        print(f"Line {i+1}: {repr(line.strip())}")
        count += 1

print(f"Total: {count}")