with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_tight.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the price rendering in renderTable
idx = c.find("'$'+r.price+'")
if idx >= 0:
    print('Found at:', idx)
    print(repr(c[idx-100:idx+200]))
else:
    # Try another pattern
    idx = c.find("r.price+\"</td>")
    print('alt search:', idx)
    if idx >= 0:
        print(repr(c[idx-100:idx+200]))
    else:
        # find all price references in html building
        idx2 = c.find("+$+r.price")
        print('pattern 2:', idx2)
        if idx2 >= 0:
            print(repr(c[idx2-100:idx2+200]))