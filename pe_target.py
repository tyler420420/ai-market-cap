with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('data-col="pe_target">PE Target</th>', 'data-col="pe_target">Post Earnings<br>Target</th>')
with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')