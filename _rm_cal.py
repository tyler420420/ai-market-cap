with open('C:/Users/Tyler_AI/Desktop/test_scanner.html', 'r', encoding='utf-8') as f:
    h = f.read()

old = '\'>Wins</a><a href="/calendar" style="background:#1f6feb;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff" onmouseover="this.style.background=\'#388bfd\'" onmouseout="this.style.background=\'#1f6feb\'">Calendar</a><button class=btn id=scanBtn'
new = '\'>Wins</a><button class=btn id=scanBtn'

if old in h:
    h = h.replace(old, new)
    with open('C:/Users/Tyler_AI/Desktop/test_scanner.html', 'w', encoding='utf-8') as f:
        f.write(h)
    print('Calendar button removed!')
else:
    print('Not found')
