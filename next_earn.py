with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('>Next<br>Report</th>', '>Next<br>Earnings</th>')
with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')