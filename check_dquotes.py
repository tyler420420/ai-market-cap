with open('ai_earnings_scanner.py','r',encoding='utf-8') as f:
    lines = f.readlines()
line = lines[533]
print('Last 30 chars:', repr(line[-30:]))
# Check for unescaped quotes in the string
# Count double quotes and escaped quotes
import re
dquotes = [m.start() for m in re.finditer(r'"', line)]
print('Double quote positions:', dquotes[:10], '...', dquotes[-5:])
print('Total double quotes:', len(dquotes))
# Look for any unescaped double quote that's not preceded by backslash
problems = []
for m in re.finditer(r'(?<!\\)"', line):
    problems.append(m.start())
print('Unescaped double quote positions (first 10):', problems[:10])