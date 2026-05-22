with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# The problematic string in the Python file (inside a double-quoted string)
old = "th[data-col='+sortCol+']"
new = 'th[data-col="\'+sortCol+\'"]'

if old in c:
    print('Found')
    c2 = c.replace(old, new, 1)
    with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
        f.write(c2)
    print('Fixed')
else:
    print('Not found - checking what IS there')
    idx = c.find("th[data-col='")
    print(repr(c[idx:idx+40]))