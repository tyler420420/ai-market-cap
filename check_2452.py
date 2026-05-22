with open('ai_earnings_scanner.py','r',encoding='utf-8') as f:
    lines = f.readlines()
line = lines[533]
# Check around the fmtEdate part
idx = line.find('fmtEdate')
if idx >= 0:
    print('fmtEdate at:', idx)
    print(repr(line[idx:idx+200]))
print('---')
# Check all positions around 2452
for i in range(2440, 2460):
    print(i, repr(line[i]))