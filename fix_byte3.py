path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

start = content.find(b"html+='<tr style")
end = content.find(b"sortBy('days_left');", start) + len(b"sortBy('days_left');")
seg = content[start:end]

# Build new segment by doing sequential replacements
# Use simple byte patterns that work

new_seg = seg

# Score
if b'<td><strong style=\\'+b'\\"color:\\'+b'\\'+b'c+\\'+b'\\';font-size:1.3em\\">\\'+b'\\'+b'r.score' in new_seg or b'<td><strong style=\\"color:\'+c+\';font-size:1.3em\\">\'+r.score' in new_seg:
    # Try actual pattern from file
    old = b'<td><strong style=\\"color:\'+c+\';font-size:1.3em\\">\'+r.score+\'</strong></td>'
    new = b'<td data-label="Score"><strong style=\\"color:\'+c+\'\\">\'+r.score+\'</strong></td>'
    if old in new_seg:
        new_seg = new_seg.replace(old, new, 1)
        print("OK: score")
    else:
        # Find it manually
        idx = new_seg.find(b"font-size:1.3em")
        if idx >= 0:
            print(f"Score found at {idx}: {repr(new_seg[idx-50:idx+100])}")
        else:
            print("MISS: score (not found)")

# Days
old = b'<td style=\\"color:\'+(r.days_left==0'
new = b'<td data-label="Days" style=\\"color:\'+(r.days_left==0'
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: days")
else:
    # Find it
    idx = new_seg.find(b"days_left=='0")
    if idx < 0:
        idx = new_seg.find(b"r.days_left+'d')")
    if idx >= 0:
        print(f"Days found at {idx}: {repr(new_seg[idx-60:idx+40])}")
    else:
        print("MISS: days")

# 3 Day Target
old = b"<td><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\\"+b'color:#00ff88\\">+\'+r.pe_upside+'%</span></td>'
new = b'<td data-label="3 Day"><strong>$'+Math.floor(b"r.pe_target")+b'</strong> <span style=\\"color:#00ff88\\">+\'+r.pe_upside+\'%</span></td>'
# Try simpler
old2 = b"<td><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\\"+b'color:#00ff88\\">+\'+r.pe_upside+'%</span></td>"
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: 3 day")
elif old2 in new_seg:
    new_seg = new_seg.replace(old2, new, 1)
    print("OK: 3 day (alt)")
else:
    idx = new_seg.find(b"r.pe_target)+")
    if idx >= 0:
        print(f"3 day found at {idx}: {repr(new_seg[idx-30:idx+100])}")
    else:
        print("MISS: 3 day")

# Strong Buy
old = b'<td style=\\"color:#00ff88\\">\'+r.sb+\'</td>'
new = b'<td data-label="Strong Buy" style=\\"color:#00ff88\\">\'+r.sb+\'</td>'
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: strong buy")
else:
    idx = new_seg.find(b"color:#00ff88")
    if idx >= 0:
        print(f"Strong buy found at {idx}: {repr(new_seg[idx-30:idx+50])}")
    else:
        print("MISS: strong buy")

# Shorts
old = b"<td style=\\'color:#fff\\'>'+r.short_int+'%</td>"
new = b"<td data-label='Shorts' style=\\'color:#fff\\'>'+r.short_int+'%</td>"
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: shorts")
else:
    idx = new_seg.find(b"r.short_int+'%")
    if idx >= 0:
        print(f"Shorts found at {idx}: {repr(new_seg[idx-40:idx+50])}")
    else:
        print("MISS: shorts")

# Trend
old = b"<td>+(r.squeeze?"
new = b"<td data-label='Trend'>+(r.squeeze?"
if old in new_seg:
    new_seg = new_seg.replace(old, new, 1)
    print("OK: trend")
else:
    idx = new_seg.find(b"r.squeeze?")
    if idx >= 0:
        print(f"Trend found at {idx}: {repr(new_seg[idx-30:idx+30])}")
    else:
        print("MISS: trend")

# Write back
content = content[:start] + new_seg + content[end:]
with open(path, 'wb') as f:
    f.write(content)
print("\nWritten!")