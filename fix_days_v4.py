c = open(r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py', 'rb').read()
old = "(r.days_left<=7?'#00ff88':'#ffcc00')"
new = "(r.days_left<=14?'#ffcc00':(r.days_left<=35?'#58a6ff':'#00ff88'))"
idx = c.find(old.encode())
print(f"Found at: {idx}")
if idx >= 0:
    c2 = c.replace(old.encode(), new.encode(), 1)
    open(r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py', 'wb').write(c2)
    print("Written")
    c3 = open(r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py', 'rb').read()
    print("New present:", new.encode() in c3)
    idx3 = c3.find(new.encode())
    print(repr(c3[idx3:idx3+80]))
else:
    print("MISS")