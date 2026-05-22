with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('>3 Day<br>Rally Target</th>', '>Great Earnings Report</th>')
with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')