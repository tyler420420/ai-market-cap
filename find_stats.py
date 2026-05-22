c = open('ai_earnings_scanner.py', encoding='utf-8').read()
idx = c.find('.stats-bar')
print('CSS found at:', idx)
# Find the corresponding HTML output - look for stats-bar in html +=
idx2 = c.find("html += '.stats-bar")
print('HTML CSS at:', idx2)
if idx2 >= 0:
    print(c[idx2:idx2+200])

# Search for where the stats bar HTML is assembled
idx3 = c.find("'<div class=stats-bar")
print('Stats bar div at:', idx3)
if idx3 >= 0:
    print(c[idx3-50:idx3+300])