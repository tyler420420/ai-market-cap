# Compare original vs changed line 534 at offset 2452
with open('ai_earnings_scanner.py','r',encoding='utf-8') as f:
    lines = f.readlines()
line = lines[533]
print('Length:', len(line))
# What character is at offset 2452 (1-indexed in Python 0-indexed = 2451)
print('Char at 2451:', repr(line[2451]))
print('Around:', repr(line[2440:2470]))