path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the renderTable section
start = content.find("html+='<tr style")
end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
seg = content[start:end]

print(f'Segment length: {len(seg)}')
print(f'data-label count: {seg.count("data-label=")}')

# Write to file for inspection
with open(r'C:\Users\Tyler_AI\ai-market-cap\js_segment.txt', 'w', encoding='utf-8') as f:
    f.write(seg)

# Now do replacements using the EXACT text from the file
# The file uses \" for double quotes in the HTML, \' for single quotes
# Each replacement is done one at a time

replacements = [
    # 1. Ticker
    ("html+=\\'<tr style=\\\\\"background:\\\\\\'\\'+bg+\\'\\\\\\"><td><strong><a href=\\\\\"https://finance.yahoo.com/quote/\\\\\\'\\'+r.ticker+\\'\\\\\\\" target=\\\\\"_blank\\\\\\\" style=\\\\\"color:#66b2ff\\\\\\\">\\\\\\'\\'+r.ticker+\\'\\\\\\</a></strong></td>\\';",
     "html+=\\'<tr style=\\\\\"background:\\\\\\'\\'+bg+\\'\\\\\\"><td data-label=\\\\\"Ticker\\\\\\"><strong><a href=\\\\\"https://finance.yahoo.com/quote/\\\\\\'\\'+r.ticker+\\'\\\\\\\" target=\\\\\"_blank\\\\\\\" style=\\\\\"color:#66b2ff\\\\\\\">\\\\\\'\\'+r.ticker+\\'\\\\\\</a></strong></td>\\';"),
]

# Better approach: use the actual characters
# From the file: html+='<tr style=\"background:'+bg+'\"><td><strong>...
# The escaped quotes in Python string: \\" and \\'

# Let's just print what the actual segment looks like for the first td
print(seg[:200])