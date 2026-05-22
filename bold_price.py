with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_tight.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Make price column bold
old = "html+='<td>'+'$'+r.price+'</td>';"
new = "html+='<td style=\"font-weight:bold\">'+'$'+r.price+'</td>';"
if old in c:
    c = c.replace(old, new, 1)
    print('Fixed price bold')
else:
    print('Pattern not found - searching...')
    idx = c.find("r.price")
    if idx >= 0:
        print(repr(c[idx-50:idx+100]))

with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_tight.html', 'w', encoding='utf-8') as f:
    f.write(c)