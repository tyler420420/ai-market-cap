import re

with open('ai_earnings_scanner.py', 'r') as f:
    content = f.read()

# Check 1: Add short_int and iv to getVal
old_getval = "'mktcap':r.mktcap'};"
new_getval = "'mktcap':r.mktcap,'short_int':r.short_int,'iv':r.iv};"
if old_getval in content and new_getval not in content:
    content = content.replace(old_getval, new_getval)
    print('1. Added short_int and iv to getVal')
else:
    print('1. Already added to getVal or pattern not found')

# Check 2: Add short_int and iv to sortAsc
old_sortasc = "||col==='mktcap';"
new_sortasc = "||col==='mktcap'||col==='short_int'||col==='iv';"
if old_sortasc in content and new_sortasc not in content:
    content = content.replace(old_sortasc, new_sortasc)
    print('2. Added short_int and iv to sortAsc')
else:
    print('2. Already added to sortAsc or pattern not found')

# Check 3: Add short_int and iv cells to renderTable
old_render = "html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';"
new_render = "html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+='<td style=\"color:#fff\">'+r.short_int+'%</td>';html+='<td style=\"color:#fff\">'+r.iv+'%</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';"
if old_render in content and new_render not in content:
    content = content.replace(old_render, new_render)
    print('3. Added short_int and iv cells to renderTable')
else:
    print('3. Already added to renderTable or pattern not found')

with open('ai_earnings_scanner.py', 'w') as f:
    f.write(content)

print('\nDone! Checking syntax...')
import ast
try:
    ast.parse(content)
    print('Syntax OK!')
except SyntaxError as e:
    print(f'Syntax Error at line {e.lineno}: {e.msg}')