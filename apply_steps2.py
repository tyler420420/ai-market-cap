content = open('ai_earnings_scanner.py').read()

# Step 1: getVal - add short_int and iv (pattern uses single quotes around mktcap key)
p1 = "r.mktcap'};return m[col]"
p1n = "r.mktcap'};return m[col]"
if p1 in content:
    print('Step1: Found pattern - replacing...')
    content = content.replace(p1, "r.mktcap,'short_int':r.short_int,'iv':r.iv};return m[col]", 1)
    print('Step1: Done')
else:
    print('Step1: NOT found')

# Step 2: sortAsc - add short_int and iv
p2 = "||col==='mktcap';"
p2n = "||col==='mktcap'||col==='short_int'||col==='iv';"
if p2 in content:
    content = content.replace(p2, p2n)
    print('Step2: Done')
else:
    print('Step2: Already done or not found')

# Step 3: renderTable - add short_int and iv cells
p3 = "html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';"
p3n = "html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+='<td style=\"color:#fff\">'+r.short_int+'%</td>';html+='<td style=\"color:#fff\">'+r.iv+'%</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';"
if p3 in content:
    content = content.replace(p3, p3n)
    print('Step3: Done')
else:
    print('Step3: Already done or not found')

with open('ai_earnings_scanner.py', 'w') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print('\nSyntax OK!')
except SyntaxError as e:
    print(f'\nSyntax Error at line {e.lineno}: {e.msg}')
    import subprocess
    subprocess.run(['git', 'checkout', '--', 'ai_earnings_scanner.py'])
    print('Restored')