with open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html', 'r', encoding='utf-8') as f:
    h = f.read()

# Fix Strong Buy badge: should be 9 (green rows, score >= 80)
h = h.replace(
    '<span style="font-weight:bold;color:#2ea043">5</span> <span style="color:#8b949e">\nStrong Buy</span>',
    '<span style="font-weight:bold;color:#2ea043">9</span> <span style="color:#8b949e">\nStrong Buy</span>'
)
# Fix Watch badge: should be 7
h = h.replace(
    '<span style="font-weight:bold;color:#58a6ff">7</span> <span style="color:#8b949e">Watch</span>',
    '<span style="font-weight:bold;color:#58a6ff">7</span> <span style="color:#8b949e">Watch</span>'
)

with open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html', 'w', encoding='utf-8') as f:
    f.write(h)

print('Fixed: Strong Buy=9, Watch=7 in Desktop file')

# Also fix scanner.html source
with open('C:\\Users\\Tyler_AI\\ai-market-cap\\scanner.html', 'r', encoding='utf-8') as f:
    h2 = f.read()

h2 = h2.replace(
    '<span style="font-weight:bold;color:#2ea043">5</span> <span style="color:#8b949e">\nStrong Buy</span>',
    '<span style="font-weight:bold;color:#2ea043">9</span> <span style="color:#8b949e">\nStrong Buy</span>'
)
h2 = h2.replace(
    '<span style="font-weight:bold;color:#58a6ff">7</span> <span style="color:#8b949e">Watch</span>',
    '<span style="font-weight:bold;color:#58a6ff">7</span> <span style="color:#8b949e">Watch</span>'
)

with open('C:\\Users\\Tyler_AI\\ai-market-cap\\scanner.html', 'w', encoding='utf-8') as f:
    f.write(h2)

print('Fixed: Strong Buy=9, Watch=7 in scanner.html')
