with open('ai_earnings_scanner.py','r',encoding='utf-8') as f:
    lines = f.readlines()
line = lines[533]
# Check all non-printable or problematic characters
for i,ch in enumerate(line):
    if i < 2440 or i > 2460:
        continue
    code = ord(ch)
    if code < 32 or code > 127:
        print(f'Pos {i}: chr({code}) = {repr(ch)}')
    elif ch in '"\'\\':
        print(f'Pos {i}: QUOTE/BS {repr(ch)} = {code}')