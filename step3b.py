# Step 3 - single quotes for style attribute
content = open('ai_earnings_scanner.py').read()
p3 = "html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';"
new_p3 = "html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+='<td style=\\'color:#fff\\'>'+r.short_int+'%</td>';html+='<td style=\\'color:#fff\\'>'+r.iv+'%</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';"
if p3 in content:
    content = content.replace(p3, new_p3)
    print('Step3: Done')
else:
    print('Step3: NOT found')

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