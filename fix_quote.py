with open('ai_earnings_scanner.py', 'rb') as f:
    content = f.read()
lines = content.split(b'\n')
# Fix line 398 - remove the backslash before the quote
lines[397] = b'    html += ".pick-banner{background:linear-gradient(135deg,#1a2a1a,#162016);border:1px solid #2ea043;border-radius:8px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;min-height:120px}"'
with open('ai_earnings_scanner.py', 'wb') as f:
    f.write(b'\n'.join(lines))
print('Fixed line 398')