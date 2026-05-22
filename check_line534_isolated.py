# Check for potential issues outside line 534
with open('ai_earnings_scanner.py','r',encoding='utf-8') as f:
    lines = f.readlines()
# Check all lines except 534 for syntax issues
import ast, tokenize
import io

# Try to parse just up to line 534
prefix = '\n'.join(lines[:533])
prefix += '\n'
try:
    ast.parse(prefix)
    print('Up to line 533: OK')
except SyntaxError as e:
    print('Error before 534:', e)

# Check line 534 in isolation
line534 = '    html += ' + lines[533].strip()
try:
    compile(line534, 'line534', 'exec')
    print('Line 534: OK')
except SyntaxError as e:
    print('Line 534 SyntaxError:', e)
    print('Offset:', e.offset)
    print('Text around offset:', repr(line534[e.offset-20:e.offset+20]))