path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Old JS days color: r.days_left==0?'#ff4444':(r.days_left<=7?'#00ff88':(r.days_left<=15?'#58a6ff':'#ffcc00'))
# New JS days color: r.days_left==0?'#ff4444':(r.days_left<=14?'#ffcc00':(r.days_left<=35?'#58a6ff':'#00ff88'))

old = "r.days_left==0?'#ff4444':(r.days_left<=7?'#00ff88':(r.days_left<=15?'#58a6ff':'#ffcc00'))"
new = "r.days_left==0?'#ff4444':(r.days_left<=14?'#ffcc00':(r.days_left<=35?'#58a6ff':'#00ff88'))"

if old in content:
    content = content.replace(old, new)
    print('OK - JS days color updated')
else:
    print('MISS - pattern not found')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)