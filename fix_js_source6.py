path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Get the segment
start = content.find("html+='<tr style")
end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
seg = content[start:end]

# Do replacements one by one using the ACTUAL patterns from the file
# From the debug output, I know exactly what the patterns look like

# Score - the td with font-size:1.3em
# Actual: <td><strong style=\"color:\'+c+\';font-size:1.3em\">\'+r.score+\'</strong></td>
old = "<td><strong style=\"color:\'+c+\';font-size:1.3em\">\'+r.score+\'</strong></td>"
new = "<td data-label=\"Score\"><strong style=\"color:\'+c+\'\">\'+r.score+\'</strong></td>"
if old in seg:
    seg = seg.replace(old, new, 1)
    print("OK: score")
else:
    print("MISS: score")

# Days
old = "<td style=\"color:\'+(r.days_left==0"
new = "<td data-label=\"Days\" style=\"color:\'+(r.days_left==0"
if old in seg:
    seg = seg.replace(old, new, 1)
    print("OK: days")
else:
    print("MISS: days")

# 3 Day Target
old = "<td><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\"color:#00ff88\">+'+r.pe_upside+'%</span></td>"
new = "<td data-label=\"3 Day\"><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\"color:#00ff88\">+'+r.pe_upside+'%</span></td>"
if old in seg:
    seg = seg.replace(old, new, 1)
    print("OK: 3 day")
else:
    print("MISS: 3 day")

# 7 Day
old = "<td>$'+Math.floor(r['3d'])+' <span style=\"color:#00ff88\">+'+r['3d_up']+'%</span></td>"
new = "<td data-label=\"7 Day\">$'+Math.floor(r['3d'])+' <span style=\"color:#00ff88\">+'+r['3d_up']+'%</span></td>"
if old in seg:
    seg = seg.replace(old, new, 1)
    print("OK: 7 day")
else:
    print("MISS: 7 day")

# 14 Day
old = "<td>$'+Math.floor(r['5d'])+' <span style=\"color:#00ff88\">+'+r['5d_up']+'%</span></td>"
new = "<td data-label=\"14 Day\">$'+Math.floor(r['5d'])+' <span style=\"color:#00ff88\">+'+r['5d_up']+'%</span></td>"
if old in seg:
    seg = seg.replace(old, new, 1)
    print("OK: 14 day")
else:
    print("MISS: 14 day")

# Strong Buy
old = "<td style=\"color:#00ff88\">\'+r.sb+\'</td>"
new = "<td data-label=\"Strong Buy\" style=\"color:#00ff88\">\'+r.sb+\'</td>"
if old in seg:
    seg = seg.replace(old, new, 1)
    print("OK: strong buy")
else:
    print("MISS: strong buy")

# Buy
old = "<td style=\"color:#58a6ff\">\'+r.buy+\'</td>"
new = "<td data-label=\"Buy\" style=\"color:#58a6ff\">\'+r.buy+\'</td>"
if old in seg:
    seg = seg.replace(old, new, 1)
    print("OK: buy")
else:
    print("MISS: buy")

# Hold
old = "<td style=\"color:#ffcc00\">\'+r.hold+\'</td>"
new = "<td data-label=\"Hold\" style=\"color:#ffcc00\">\'+r.hold+\'</td>"
if old in seg:
    seg = seg.replace(old, new, 1)
    print("OK: hold")
else:
    print("MISS: hold")

# Sell
old = "<td style=\"color:#ff6b6b\">\'+r.sell+\'</td>"
new = "<td data-label=\"Sell\" style=\"color:#ff6b6b\">\'+r.sell+\'</td>"
if old in seg:
    seg = seg.replace(old, new, 1)
    print("OK: sell")
else:
    print("MISS: sell")

# Shorts
old = "<td style='color:#fff'>'+r.short_int+'%</td>"
new = "<td data-label='Shorts' style='color:#fff'>'+r.short_int+'%</td>"
if old in seg:
    seg = seg.replace(old, new, 1)
    print("OK: shorts")
else:
    print("MISS: shorts")

# IV
old = "<td style='color:#fff'>'+r.iv+'%</td>"
new = "<td data-label='IV' style='color:#fff'>'+r.iv+'%</td>"
if old in seg:
    seg = seg.replace(old, new, 1)
    print("OK: iv")
else:
    print("MISS: iv")

# Trend
old = "<td>+(r.squeeze?"
new = "<td data-label='Trend'>+(r.squeeze?"
if old in seg:
    seg = seg.replace(old, new, 1)
    print("OK: trend")
else:
    print("MISS: trend")

# Write back
content = content[:start] + seg + content[end:]
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("\nWritten!")