with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the sortCol selector
idx = c.find("th[data-col='+sortCol+']")
print('Found at:', idx)
if idx >= 0:
    with open('sortcol_raw.txt', 'w', encoding='utf-8') as f:
        f.write(c[idx-30:idx+50])
    print('Written')
else:
    print('NOT FOUND')
    # Try to find th[data-col= anywhere
    idx2 = c.find('th[data-col=')
    print('th[data-col= at:', idx2)
    if idx2 >= 0:
        with open('sortcol_raw.txt', 'w', encoding='utf-8') as f:
            f.write(c[idx2:idx2+100])