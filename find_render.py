with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_tight.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find renderTable function
idx = c.find("function renderTable")
if idx >= 0:
    # Show first 2000 chars of renderTable
    print(repr(c[idx:idx+2000]))