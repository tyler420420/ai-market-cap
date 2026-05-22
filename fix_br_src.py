c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
# Change to use <br> directly instead of \n in Python
c=c.replace(
    "(lambda ed: ed[5:10].replace('-', chr(45)) + chr(10) + ed[:4] if ed else '')(stock.earnings_date)",
    "(lambda ed: '<br>'.join([ed[5:10].replace('-', chr(45)), ed[:4]]) if ed else '')(stock.earnings_date)"
)
# Also change JS to just display the earnings_date (Python already puts <br> in it)
c=c.replace(
    "html+='<td class=earn-cell>'+r.earnings_date+'</td>'",
    "html+='<td class=earn-cell>'+r.earnings_date+'</td>'"
)
compile(c,'x','exec')
print('OK')
with open('ai_earnings_scanner.py','w',encoding='utf-8') as f:
    f.write(c)