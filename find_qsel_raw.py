with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()
idx = c.find('document.querySelector')
print('Found at:', idx)
# Write 100 chars around it to file
with open('qsel_raw.txt', 'w', encoding='utf-8') as f:
    f.write(c[idx-20:idx+60])
print('Written')