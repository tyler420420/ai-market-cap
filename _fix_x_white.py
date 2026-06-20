with open('C:/Users/Tyler_AI/Desktop/test_scanner.html', 'r', encoding='utf-8') as f:
    h = f.read()

old = 'background:#5741d9;color:#000;padding:3px 10px;border-radius:5px;border:1px solid #fff;font-size:0.82em;font-weight:bold;text-decoration:none" onmouseover="this.style.background=\'#6e55e0\'" onmouseout="this.style.background=\'#5741d9\'">Follow Us On X</a>'
new = 'background:#5741d9;color:#fff;padding:3px 10px;border-radius:5px;border:1px solid #fff;font-size:0.82em;font-weight:bold;text-decoration:none" onmouseover="this.style.background=\'#6e55e0\'" onmouseout="this.style.background=\'#5741d9\'">Follow Us On X</a>'

if old in h:
    h = h.replace(old, new)
    with open('C:/Users/Tyler_AI/Desktop/test_scanner.html', 'w', encoding='utf-8') as f:
        f.write(h)
    print('Follow Us On X: white text back')
else:
    print('Pattern not found')
