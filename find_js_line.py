with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()
# Find the exact line starting with the JS
idx = c.find("html += \"var sortCol='days_left'")
with open('js_line.txt', 'w', encoding='utf-8') as out:
    out.write(c[idx:idx+200])
print('Written, length:', len(c[idx:idx+200]))