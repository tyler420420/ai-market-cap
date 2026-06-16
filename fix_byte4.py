path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

start = content.find(b"html+='<tr style")
end = content.find(b"sortBy('days_left');", start) + len(b"sortBy('days_left');")
seg = content[start:end]

# Replace by finding start/end of each td and inserting data-label
# Pattern: find "<td" followed by ">" — insert data-label between them

new_seg = bytearray(seg)
changes = 0

# We need to be careful about the order - we want to insert data-label
# before the first ">" of each td that doesn't already have it

# Approach: find each <td that doesn't have data-label, and insert the label

# Pattern for each column (find by unique surrounding text):
# Score: find "font-size:1.3em" and go backwards to find "<td"
# Days: find "r.days_left+'d'" and go backwards
# etc.

def find_and_replace(data, search_bytes, insert_bytes, count=1):
    idx = 0
    made = 0
    while made < count:
        found = data.find(search_bytes, idx)
        if found < 0:
            break
        # Insert before the found position
        data[found:found] = insert_bytes
        idx = found + len(search_bytes) + len(insert_bytes)
        made += 1
    return made

# Score: find "font-size:1.3em" and insert data-label before the <td that precedes it
# The td starts at the < before this pattern
idx = new_seg.find(b"font-size:1.3em")
if idx >= 0:
    # Find <td before this
    td_start = new_seg.rfind(b"<td", 0, idx)
    if td_start >= 0:
        # Check if it already has data-label
        if b"data-label" not in new_seg[td_start:idx]:
            label = b' data-label="Score"'
            new_seg = new_seg[:td_start+3] + label + new_seg[td_start+3:]
            changes += 1
            print("OK: score")
        else:
            print("ALREADY: score")
    else:
        print("MISS: score td start")
else:
    print("MISS: score pattern")

# Days
idx = new_seg.find(b"r.days_left+'d')")
if idx >= 0:
    td_start = new_seg.rfind(b"<td", 0, idx)
    if td_start >= 0:
        if b"data-label" not in new_seg[td_start:idx]:
            label = b' data-label="Days"'
            new_seg = new_seg[:td_start+3] + label + new_seg[td_start+3:]
            changes += 1
            print("OK: days")
        else:
            print("ALREADY: days")
    else:
        print("MISS: days td start")
else:
    print("MISS: days pattern")

# 3 Day Target - find the <td before r.pe_target
idx = new_seg.find(b"r.pe_target)+")
if idx >= 0:
    td_start = new_seg.rfind(b"<td", 0, idx)
    if td_start >= 0 and b"data-label" not in new_seg[td_start:idx]:
        label = b' data-label="3 Day"'
        new_seg = new_seg[:td_start+3] + label + new_seg[td_start+3:]
        changes += 1
        print("OK: 3 day")
    else:
        print(f"ALREADY or MISS: 3 day (td_start={td_start})")
else:
    print("MISS: 3 day pattern")

# 7 Day
idx = new_seg.find(b"r['3d'])+")
if idx >= 0:
    td_start = new_seg.rfind(b"<td", 0, idx)
    if td_start >= 0 and b"data-label" not in new_seg[td_start:idx]:
        label = b" data-label='7 Day'"
        new_seg = new_seg[:td_start+3] + label + new_seg[td_start+3:]
        changes += 1
        print("OK: 7 day")
    else:
        print("ALREADY or MISS: 7 day")
else:
    print("MISS: 7 day pattern")

# 14 Day
idx = new_seg.find(b"r['5d'])+")
if idx >= 0:
    td_start = new_seg.rfind(b"<td", 0, idx)
    if td_start >= 0 and b"data-label" not in new_seg[td_start:idx]:
        label = b" data-label='14 Day'"
        new_seg = new_seg[:td_start+3] + label + new_seg[td_start+3:]
        changes += 1
        print("OK: 14 day")
    else:
        print("ALREADY or MISS: 14 day")
else:
    print("MISS: 14 day pattern")

# Strong Buy
idx = new_seg.find(b"r.sb+'%</td>")
if idx >= 0:
    td_start = new_seg.rfind(b"<td", 0, idx)
    if td_start >= 0 and b"data-label" not in new_seg[td_start:idx]:
        label = b' data-label="Strong Buy"'
        new_seg = new_seg[:td_start+3] + label + new_seg[td_start+3:]
        changes += 1
        print("OK: strong buy")
    else:
        print("ALREADY or MISS: strong buy")
else:
    print("MISS: strong buy pattern")

# Buy
idx = new_seg.find(b"r.buy+'%</td>")
if idx >= 0:
    td_start = new_seg.rfind(b"<td", 0, idx)
    if td_start >= 0 and b"data-label" not in new_seg[td_start:idx]:
        label = b' data-label="Buy"'
        new_seg = new_seg[:td_start+3] + label + new_seg[td_start+3:]
        changes += 1
        print("OK: buy")
    else:
        print("ALREADY or MISS: buy")
else:
    print("MISS: buy pattern")

# Hold
idx = new_seg.find(b"r.hold+'%</td>")
if idx >= 0:
    td_start = new_seg.rfind(b"<td", 0, idx)
    if td_start >= 0 and b"data-label" not in new_seg[td_start:idx]:
        label = b' data-label="Hold"'
        new_seg = new_seg[:td_start+3] + label + new_seg[td_start+3:]
        changes += 1
        print("OK: hold")
    else:
        print("ALREADY or MISS: hold")
else:
    print("MISS: hold pattern")

# Sell
idx = new_seg.find(b"r.sell+'%</td>")
if idx >= 0:
    td_start = new_seg.rfind(b"<td", 0, idx)
    if td_start >= 0 and b"data-label" not in new_seg[td_start:idx]:
        label = b' data-label="Sell"'
        new_seg = new_seg[:td_start+3] + label + new_seg[td_start+3:]
        changes += 1
        print("OK: sell")
    else:
        print("ALREADY or MISS: sell")
else:
    print("MISS: sell pattern")

# Shorts
idx = new_seg.find(b"r.short_int+'%</td>")
if idx >= 0:
    td_start = new_seg.rfind(b"<td", 0, idx)
    if td_start >= 0 and b"data-label" not in new_seg[td_start:idx]:
        label = b" data-label='Shorts'"
        new_seg = new_seg[:td_start+3] + label + new_seg[td_start+3:]
        changes += 1
        print("OK: shorts")
    else:
        print("ALREADY or MISS: shorts")
else:
    print("MISS: shorts pattern")

# IV
idx = new_seg.find(b"r.iv+'%</td>")
if idx >= 0:
    td_start = new_seg.rfind(b"<td", 0, idx)
    if td_start >= 0 and b"data-label" not in new_seg[td_start:idx]:
        label = b" data-label='IV'"
        new_seg = new_seg[:td_start+3] + label + new_seg[td_start+3:]
        changes += 1
        print("OK: iv")
    else:
        print("ALREADY or MISS: iv")
else:
    print("MISS: iv pattern")

# Trend
idx = new_seg.find(b"r.squeeze?")
if idx >= 0:
    td_start = new_seg.rfind(b"<td", 0, idx)
    if td_start >= 0 and b"data-label" not in new_seg[td_start:idx]:
        label = b" data-label='Trend'"
        new_seg = new_seg[:td_start+3] + label + new_seg[td_start+3:]
        changes += 1
        print("OK: trend")
    else:
        print("ALREADY or MISS: trend")
else:
    print("MISS: trend pattern")

print(f"\nTotal: {changes} replacements")
content = content[:start] + bytes(new_seg) + content[end:]
with open(path, 'wb') as f:
    f.write(content)
print("Written!")