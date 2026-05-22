with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Write the exact content of line 529 (index 528)
with open('line529_raw.txt', 'w', encoding='utf-8') as f:
    f.write(lines[528])

print('Done, length:', len(lines[528]))