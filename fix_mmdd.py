with open('ai_earnings_scanner.py','r',encoding='utf-8') as f:
    c=f.read()
# Format earnings_date as MM-DD\nYYYY
old = "'earnings_date': (lambda ed: ed[5:].replace('-', chr(45)) + chr(10) + ed[:4] if ed else '')(stock.earnings_date),"
new = "'earnings_date': (lambda ed: ed[5:10].replace('-', chr(45)) + chr(10) + ed[:4] if ed else '')(stock.earnings_date),"
c=c.replace(old,new)
compile(c,'x','exec')
print('Syntax OK')
with open('ai_earnings_scanner.py','w',encoding='utf-8') as f:
    f.write(c)