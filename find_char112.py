# Get exact position 112 of line 534
with open('ai_earnings_scanner.py','r',encoding='utf-8') as f:
    lines = f.readlines()
line = lines[533]
print('Char at 112:', repr(line[112]))
print('Around 112:', repr(line[100:150]))