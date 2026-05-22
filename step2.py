# Step 2 only
content = open('ai_earnings_scanner.py').read()
p2 = "||col==='mktcap';"
if p2 in content:
    content = content.replace(p2, "||col==='mktcap'||col==='short_int'||col==='iv';")
    print('Step2: Done')
else:
    print('Step2: NOT found')

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