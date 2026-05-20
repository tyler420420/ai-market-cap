import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('ai_earnings_web.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

old = "window.location='scan/latest?_='+Date.now();},3000);"
new = "window.location='/scanner';},3000);"

if old in content:
    content = content.replace(old, new)
    with open('ai_earnings_web.html', 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print('Fixed: reload goes to /scanner')
else:
    print('Not found - checking...')
    idx = content.find('window.location')
    print(content[idx:idx+100])