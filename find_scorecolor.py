with open('ai_earnings_scanner.py','r',encoding='utf-8') as f:
    lines = f.readlines()

# Find scoreColor line
for i,l in enumerate(lines):
    if 'scoreColor' in l and 'function' in l:
        print(i+1, repr(l[:150]))