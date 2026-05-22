c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
old = '<meta charset="UTF-8"><title>\' + SCANNER_TITLE + \'</title>'
new = '<meta name="viewport" content="width=device-width, initial-scale=1"><meta charset="UTF-8"><title>\' + SCANNER_TITLE + \'</title>'
if old in c:
    c=c.replace(old,new)
    open('ai_earnings_scanner.py','w',encoding='utf-8').write(c)
    print('Done')
else:
    idx=c.find('<meta charset')
    print(repr(c[idx:idx+60]))