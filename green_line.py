with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_tight.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Change the border-right to glow green
old = 'td:nth-child(6){border-right:2px solid #30363d}'
new = 'td:nth-child(6){border-right:2px solid #3fb950;box-shadow:1px 0 8px rgba(63,185,80,0.5)}'
c = c.replace(old, new, 1)

with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_tight.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')