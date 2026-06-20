with open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html', 'r', encoding='utf-8') as f:
    h = f.read()

# Strong Buy = 13 (score >= 75)
h = h.replace(
    '<span style="font-weight:bold;color:#2ea043">9</span> <span style="color:#8b949e">\nStrong Buy</span>',
    '<span style="font-weight:bold;color:#2ea043">13</span> <span style="color:#8b949e">\nStrong Buy</span>'
)

with open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html', 'w', encoding='utf-8') as f:
    f.write(h)

# Also fix scanner.html
with open('C:\\Users\\Tyler_AI\\ai-market-cap\\scanner.html', 'r', encoding='utf-8') as f:
    h2 = f.read()

h2 = h2.replace(
    '<span style="font-weight:bold;color:#2ea043">9</span> <span style="color:#8b949e">\nStrong Buy</span>',
    '<span style="font-weight:bold;color:#2ea043">13</span> <span style="color:#8b949e">\nStrong Buy</span>'
)

with open('C:\\Users\\Tyler_AI\\ai-market-cap\\scanner.html', 'w', encoding='utf-8') as f:
    f.write(h2)

print('Fixed: Strong Buy=13, Watch=7')
