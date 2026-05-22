with open('ai_earnings_scanner.py', 'r') as f:
    content = f.read()

# Step 1: getVal - add short_int and iv
p1 = "'mktcap':r.mktcap};"
p1n = "'mktcap':r.mktcap,'short_int':r.short_int,'iv':r.iv};"
if p1 in content and p1n not in content:
    content = content.replace(p1, p1n)
    print('Step1: Added short_int and iv to getVal')
elif p1n in content:
    print('Step1: Already done')
else:
    print('Step1: Pattern not found')

# Step 2: sortAsc - add short_int and iv
p2 = "||col==='mktcap';"
p2n = "||col==='mktcap'||col==='short_int'||col==='iv';"
if p2 in content and p2n not in content:
    content = content.replace(p2, p2n)
    print('Step2: Added short_int and iv to sortAsc')
elif p2n in content:
    print('Step2: Already done')
else:
    print('Step2: Pattern not found')

# Step 3: renderTable - add short_int and iv cells
p3 = "html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';"
p3n = "html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+='<td style=\"color:#fff\">'+r.short_int+'%</td>';html+='<td style=\"color:#fff\">'+r.iv+'%</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';"
if p3 in content and p3n not in content:
    content = content.replace(p3, p3n)
    print('Step3: Added short_int and iv cells to renderTable')
elif p3n in content:
    print('Step3: Already done')
else:
    print('Step3: Pattern not found')
    # debug
    idx = content.find('fmtMktcap(r.mktcap)')
    if idx >= 0:
        print('Found fmtMktcap at:', repr(content[idx-20:idx+80]))

with open('ai_earnings_scanner.py', 'w') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print('\nSyntax OK!')
except SyntaxError as e:
    print(f'\nSyntax Error at line {e.lineno}: {e.msg}')
    # fix it - restore and try step by step
    import subprocess
    subprocess.run(['git', 'checkout', '--', 'ai_earnings_scanner.py'])
    print('Restored via git')