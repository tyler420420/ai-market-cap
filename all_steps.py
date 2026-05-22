# All 3 steps combined
content = open('ai_earnings_scanner.py').read()

# Step 1: getVal
p1 = "r.mktcap'};return m[col]"
content = content.replace(p1, "r.mktcap,'short_int':r.short_int,'iv':r.iv};return m[col]", 1)
print('Step1: getVal done')

# Step 2: sortAsc
p2 = "||col==='mktcap';"
content = content.replace(p2, "||col==='mktcap'||col==='short_int'||col==='iv';")
print('Step2: sortAsc done')

# Step 3: renderTable - single quotes for style
p3 = "html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';"
new_p3 = "html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+='<td style=\\'color:#fff\\'>'+r.short_int+'%</td>';html+='<td style=\\'color:#fff\\'>'+r.iv+'%</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';"
content = content.replace(p3, new_p3)
print('Step3: renderTable done')

with open('ai_earnings_scanner.py', 'w') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print('\nSyntax OK!')
except SyntaxError as e:
    print(f'\nSyntax Error at line {e.lineno}')
    import subprocess
    subprocess.run(['git', 'checkout', '--', 'ai_earnings_scanner.py'])