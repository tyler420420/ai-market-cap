c = open('ai_earnings_today.html', encoding='utf-8').read()
old = "body{font-family:Segoe UI,Arial,sans-serif;background:#0d1117;color:#c9d1d9;padding:20px}"
new = "body{font-family:Segoe UI,Arial,sans-serif;background:#0d1117;color:#c9d1d9;padding:0;margin:0}"
if old in c:
    c = c.replace(old, new)
    open('ai_earnings_today.html', 'w', encoding='utf-8').write(c)
    print('Body padding removed')
else:
    print('NOT found')