path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

start = content.find(b"html+='<tr style")
end = content.find(b"sortBy('days_left');", start) + len(b"sortBy('days_left');")
seg = content[start:end]

# Build new segment by replacing bytes directly
# Use raw byte strings with proper escaping

new_seg = seg

# Score
old = b'<td><strong style=\\"color:\'+c+\';font-size:1.3em\\">\'+r.score+\'</strong></td>'
new = b'<td data-label="Score"><strong style=\\"color:\'+c+\'\\">\'+r.score+\'</strong></td>'
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: score")
else:
    print("MISS: score")

# Days
old = b'<td style=\\"color:\'+(r.days_left==0'
new = b'<td data-label="Days" style=\\"color:\'+(r.days_left==0'
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: days")
else:
    print("MISS: days")

# 3 Day Target
old = b"<td><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\\"+b'color:#00ff88\\">+\'+r.pe_upside+'%</span></td>'
new = b'<td data-label="3 Day"><strong>$'+Math.floor(b"r.pe_target")+b'</strong> <span style=\\"color:#00ff88\\">+\'+r.pe_upside+\'%</span></td>'
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: 3 day")
else:
    print("MISS: 3 day")

# 7 Day
old = b"<td>$'+Math.floor(r['3d'])+' <span style=\\"+b'color:#00ff88\\">+\'+r[\'3d_up\']+\'%</span></td>'
new = b"<td data-label='7 Day'>$'+Math.floor(r['3d'])+' <span style=\\"+b'color:#00ff88\\">+\'+r[\'3d_up\']+\'%</span></td>'
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: 7 day")
else:
    print("MISS: 7 day")

# 14 Day
old = b"<td>$'+Math.floor(r['5d'])+' <span style=\\"+b'color:#00ff88\\">+\'+r[\'5d_up\']+\'%</span></td>'
new = b"<td data-label='14 Day'>$'+Math.floor(r['5d'])+' <span style=\\"+b'color:#00ff88\\">+\'+r[\'5d_up\']+\'%</span></td>'
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: 14 day")
else:
    print("MISS: 14 day")

# Strong Buy
old = b'<td style=\\"color:#00ff88\\">\'+r.sb+\'</td>'
new = b'<td data-label="Strong Buy" style=\\"color:#00ff88\\">\'+r.sb+\'</td>'
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: strong buy")
else:
    print("MISS: strong buy")

# Buy
old = b'<td style=\\"color:#58a6ff\\">\'+r.buy+\'</td>'
new = b'<td data-label="Buy" style=\\"color:#58a6ff\\">\'+r.buy+\'</td>'
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: buy")
else:
    print("MISS: buy")

# Hold
old = b'<td style=\\"color:#ffcc00\\">\'+r.hold+\'</td>'
new = b'<td data-label="Hold" style=\\"color:#ffcc00\\">\'+r.hold+\'</td>'
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: hold")
else:
    print("MISS: hold")

# Sell
old = b'<td style=\\"color:#ff6b6b\\">\'+r.sell+\'</td>'
new = b'<td data-label="Sell" style=\\"color:#ff6b6b\\">\'+r.sell+\'</td>'
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: sell")
else:
    print("MISS: sell")

# Shorts
old = b"<td style=\\'color:#fff\\'>'+r.short_int+'%</td>"
new = b"<td data-label='Shorts' style=\\'color:#fff\\'>'+r.short_int+'%</td>"
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: shorts")
else:
    print("MISS: shorts")

# IV
old = b"<td style=\\'color:#fff\\'>'+r.iv+'%</td>"
new = b"<td data-label='IV' style=\\'color:#fff\\'>'+r.iv+'%</td>"
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: iv")
else:
    print("MISS: iv")

# Trend
old = b"<td>+(r.squeeze?"
new = b"<td data-label='Trend'>+(r.squeeze?"
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: trend")
else:
    print("MISS: trend")

# Write back
content = content[:start] + new_seg + content[end:]
with open(path, 'wb') as f:
    f.write(content)
print("\nWritten!")