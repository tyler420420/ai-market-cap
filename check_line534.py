# Read line 534 directly
with open('ai_earnings_scanner.py','r',encoding='utf-8') as f:
    lines = f.readlines()
line = lines[533]  # 0-indexed
print('Length:', len(line))
print('Last 100 chars:', repr(line[-100:]))
# Look for syntax issues in the string
# Check if there are unescaped quotes
import re
# Find any single-quote issues in the HTML string
idx = line.find("white-space")
print('white-space at:', idx)
if idx>0:
    print(repr(line[idx:idx+50]))