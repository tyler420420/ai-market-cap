with open('ai_earnings_scanner.py','r',encoding='utf-8') as f:
    content = f.read()

# The style with font-size:0.85em has a semicolon - can't use in single-quoted Python string
# Remove the style from the td cell - it will just display normally with the newline
content = content.replace(
    "html+='<td style=\"font-size:0.85em\">'+r.earnings_date.replace(chr(10),'<br>')+'</td>'",
    "html+='<td style=\"font-size:0.82em\">'+r.earnings_date.replace(chr(10),'<br>')+'</td>'"
)
# Still has semicolon issue. Use a different approach - use HTML entities for semicolon
content = content.replace(
    "html+='<td style=\"font-size:0.85em\">'+r.earnings_date.replace(chr(10),'<br>')+'</td>'",
    "html+='<td class=earn-cell>'+r.earnings_date.replace(chr(10),'<br>')+'</td>'"
)

# Add CSS for .earn-cell
content = content.replace(
    '.note{margin-top:20px;padding:12px 18px;background:#161b22;border-radius:8px;font-size:0.82em;color:#8b949e;border:1px solid #30363d}',
    '.note{margin-top:20px;padding:12px 18px;background:#161b22;border-radius:8px;font-size:0.82em;color:#8b949e;border:1px solid #30363d}.earn-cell{font-size:0.82em}'
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