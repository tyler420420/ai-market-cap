with open('ai_earnings_57day_20260520_0213.html', 'r', encoding='utf-8') as f:
    c = f.read()
with open('quick_check.txt', 'w', encoding='utf-8') as out:
    out.write('onclick on TH: ' + str('onclick="sortBy' in c) + '\n')
    out.write('sortBy function exists: ' + str('function sortBy' in c) + '\n')
    out.write('tbody innerHTML: ' + str('tbody.innerHTML' in c) + '\n')
    idx = c.find('<th onclick')
    out.write('First TH onclick: ' + c[idx:idx+50] + '\n')
    idx2 = c.find("sortBy('days_left')")
    out.write('sortBy(days_left) call: ' + c[idx2-30:idx2+30] + '\n')
print('Done')