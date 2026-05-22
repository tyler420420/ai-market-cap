with open('ai_earnings_scanner.py','r',encoding='utf-8') as f:
    content = f.read()

# Fix the semicolon in style attribute
content = content.replace(
    "html+='<td style=\"font-size:0.85em\">'+r.earnings_date+'</td>'",
    "html+='<td style=\"font-size:0.85em\">'+r.earnings_date.replace(chr(10),'<br>')+'</td>'"
)

# Also add the Python earnings_date formatting
content = content.replace(
    "'earnings_date': stock.earnings_date,",
    "'earnings_date': (lambda ed: ed[5:].replace('-', chr(45)) + chr(10) + ed[:4] if ed else '')(stock.earnings_date),"
)

try:
    compile(content, 'x', 'exec')
    print('Syntax OK')
    with open('ai_earnings_scanner.py','w',encoding='utf-8') as f:
        f.write(content)
    print('Saved')
except SyntaxError as e:
    print('Error at line', e.lineno, 'offset', e.offset)
    lines = content.split('\n')
    print(repr(lines[e.lineno-1][e.offset-20:e.offset+20]))