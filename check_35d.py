with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

idx = c.find("r['3d']")
print(repr(c[idx-30:idx+100]))
print()
idx2 = c.find("r['5d']")
print(repr(c[idx2-30:idx2+100]))