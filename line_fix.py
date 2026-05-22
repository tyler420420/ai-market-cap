with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_tight.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Add vertical line between Price and PE Target columns
# Add border-right to the price column th and td
# Find the price column in CSS and add border-right
old = 'td{padding:10px 10px;border-bottom:1px solid #30363d;font-size:0.88em;color:#fff}'
new = 'td{padding:10px 10px;border-bottom:1px solid #30363d;font-size:0.88em;color:#fff}td:nth-child(6){border-right:2px solid #30363d}'
c = c.replace(old, new, 1)

with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_tight.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')