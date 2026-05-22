c = open('ai_earnings_scanner.py', encoding='utf-8').read()
old = "';font-weight:bold\">'+r.days_left+'d</td>'"
new = "';cursor:pointer;text-decoration:underline' onclick=sortBy('days_left')>'+r.days_left+'d</td>'"
if old in c:
    c = c.replace(old, new)
    open('ai_earnings_scanner.py', 'w', encoding='utf-8').write(c)
    print('Source updated')
else:
    print('NOT found in source')