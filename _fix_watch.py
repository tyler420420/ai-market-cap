with open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html', 'r', encoding='utf-8') as f:
    h = f.read()

# Fix Watch badge: should be 7, not 5
h = h.replace(
    '<span style="font-weight:bold;color:#58a6ff">5</span> <span style="color:#8b949e">Watch</span>',
    '<span style="font-weight:bold;color:#58a6ff">7</span> <span style="color:#8b949e">Watch</span>'
)

with open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html', 'w', encoding='utf-8') as f:
    f.write(h)

print('Fixed: Watch now shows 7')
