# Step 1 only
content = open('ai_earnings_scanner.py').read()
p1 = "r.mktcap'};return m[col]"
if p1 in content:
    content = content.replace(p1, "r.mktcap,'short_int':r.short_int,'iv':r.iv};return m[col]", 1)
    print('Done')
else:
    print('NOT found')

with open('ai_earnings_scanner.py', 'w') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print('Syntax OK!')
except SyntaxError as e:
    print(f'Syntax Error at line {e.lineno}')
    import subprocess
    subprocess.run(['git', 'checkout', '--', 'ai_earnings_scanner.py'])