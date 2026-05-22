with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Count occurrences of different patterns
count1 = c.count("'+sortCol+'")
count2 = c.count('"+sortCol+"')
count3 = c.count("\"'+sortCol+'\"")
print("'+sortCol+':", count1)
print('"+sortCol+":', count2)
print('"\'+sortCol+\'"', count3)

# Find all occurrences of sortCol in the JS block
idx = c.find("var sortCol='days_left'")
# Look in next 500 chars for sortCol selector
chunk = c[idx:idx+500]
import re
for m in re.finditer(r'[^\n]{0,30}sortCol[^\n]{0,30}', chunk):
    print(repr(m.group()))