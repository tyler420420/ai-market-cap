with open('ai_earnings_scanner.py', 'r') as f:
    lines = f.readlines()

line538 = lines[537]

# Remove backslashes at positions: 2870, 2879, 2925, 2934, 2973
# Need to process from highest position to lowest to preserve positions
positions = [2973, 2934, 2925, 2879, 2870]

new_line538 = line538
for pos in positions:
    if pos < len(new_line538) and new_line538[pos] == chr(92):
        new_line538 = new_line538[:pos] + new_line538[pos+1:]

backslash_count = new_line538.count(chr(92))
print(f"Backslashes remaining: {backslash_count}")

if backslash_count == 0:
    lines[537] = new_line538
    with open('ai_earnings_scanner.py', 'w') as f:
        f.writelines(lines)
    print("Fixed!")
else:
    print("Still has backslashes")
    for i, c in enumerate(new_line538):
        if c == chr(92):
            print(f"  At {i}: {repr(new_line538[i-10:i+30])}")