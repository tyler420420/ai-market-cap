with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('data-col="price">Price</th>', 'data-col="price">Current<br>Price</th>')
with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')