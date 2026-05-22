with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Break Days Left into two lines
c = c.replace(">Days Left</th>", ">Days<br>Left</th>")

with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')