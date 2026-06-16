import re
c = open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'r', encoding='utf-8').read()

# Find IPOs section
idx = c.find('IPO')
if idx >= 0:
    print("IPO section:")
    print(c[idx-50:idx+500])
else:
    print("No IPO found")
    # Search for upcoming section
    idx = c.find('upcoming')
    print("upcoming:", idx)
    idx = c.find('IPO')
    print("IPO:", idx)
    # Find any section that might be the cards
    for keyword in ['IPO', 'upcoming', 'cards', 'card']:
        idx2 = c.find(keyword, idx+1 if idx >= 0 else 0)
        if idx2 >= 0:
            print(f"Found '{keyword}' at {idx2}:", c[idx2:idx2+200])