import re
with open('ai_earnings_scanner.py', encoding='utf-8') as f:
    src = f.read()

# Find all html+= lines with style= attributes
single_q = re.findall(r"html\+\='[^']*style='[^']*'", src)
double_q = re.findall(r'html\+\="[^"]*style="[^"]*"', src)

print(f'Single-quoted style patterns: {len(single_q)}')
for m in single_q[:3]:
    print(f'  {m[:120]}')

print(f'\nDouble-quoted style patterns: {len(double_q)}')
for m in double_q[:3]:
    print(f'  {m[:120]}')

# Check the specific problematic line - look for style=' inside the long line 821
line821_start = src.find('html += "var sortCol')
line821 = src[line821_start:line821_start+200]
print(f'\nLine 821 snippet: {repr(line821[:200])}')
