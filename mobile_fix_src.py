c = open('ai_earnings_scanner.py', encoding='utf-8').read()
old = "@media(max-width:768px){body,table,div{max-width:100%!important;box-sizing:border-box}body{padding:8px!important}"
new = "@media(max-width:768px){body,table,div{max-width:100%!important;box-sizing:border-box}body{padding:0!important}.header{border-radius:0;border-left:none;border-right:none}.updated,.stats-bar,.note,.disclaimer{padding-left:8px!important;padding-right:8px!important}"
if old in c:
    c = c.replace(old, new)
    open('ai_earnings_scanner.py', 'w', encoding='utf-8').write(c)
    print('Source updated')
else:
    print('NOT found')