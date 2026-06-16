path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check line 804
print(f'Total lines: {len(lines)}')
if len(lines) >= 804:
    line = lines[803]
    print(f'Line 804: {repr(line[:200])}')
    # Check if it has unclosed quotes
    # Count single quotes in the line
    sq = line.count("'")
    dq = line.count('"')
    print(f'Single quotes: {sq}, Double quotes: {dq}')
    # Try to find where the problem is
    # The line should be: html += "var sortCol='score';..."
    # If there's a missing quote, the parser will complain
    if sq % 2 != 0:
        print('ODD number of single quotes!')
    if dq % 2 != 0:
        print('ODD number of double quotes!')