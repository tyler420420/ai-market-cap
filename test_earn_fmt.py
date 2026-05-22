with open('ai_earnings_scanner.py','r',encoding='utf-8') as f:
    content = f.read()

# Fix 8: earnings_date formatting - use newline in string
content = content.replace(
    "'earnings_date': stock.earnings_date,",
    "'earnings_date': (lambda ed: ed[5:].replace('-', chr(45)) + chr(10) + ed[:4] if ed else '')(stock.earnings_date),"
)

try:
    compile(content, 'x', 'exec')
    print('Syntax OK')
    with open('ai_earnings_scanner.py','w',encoding='utf-8') as f:
        f.write(content)
except SyntaxError as e:
    print('Error at line', e.lineno, 'offset', e.offset)