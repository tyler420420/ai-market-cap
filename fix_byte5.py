path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

start = content.find(b"html+='<tr style")
end = content.find(b"sortBy('days_left');", start) + len(b"sortBy('days_left');")
seg = content[start:end]

new_seg = bytearray(seg)

# Find strong buy - looking for r.sb without the %
idx = new_seg.find(b"color:#00ff88")
if idx >= 0:
    td_start = new_seg.rfind(b"<td", 0, idx)
    if td_start >= 0 and b"data-label" not in new_seg[td_start:idx]:
        label = b' data-label="Strong Buy"'
        new_seg = new_seg[:td_start+3] + label + new_seg[td_start+3:]
        print("OK: strong buy")
    else:
        print(f"ALREADY or MISS: strong buy (td_start={td_start})")
else:
    print("MISS: strong buy")

# Buy
idx = new_seg.find(b"color:#58a6ff")
if idx >= 0:
    td_start = new_seg.rfind(b"<td", 0, idx)
    if td_start >= 0 and b"data-label" not in new_seg[td_start:idx]:
        label = b' data-label="Buy"'
        new_seg = new_seg[:td_start+3] + label + new_seg[td_start+3:]
        print("OK: buy")
    else:
        print("ALREADY or MISS: buy")
else:
    print("MISS: buy")

# Hold
idx = new_seg.find(b"color:#ffcc00")
if idx >= 0:
    td_start = new_seg.rfind(b"<td", 0, idx)
    if td_start >= 0 and b"data-label" not in new_seg[td_start:idx]:
        label = b' data-label="Hold"'
        new_seg = new_seg[:td_start+3] + label + new_seg[td_start+3:]
        print("OK: hold")
    else:
        print("ALREADY or MISS: hold")
else:
    print("MISS: hold")

# Sell
idx = new_seg.find(b"color:#ff6b6b")
if idx >= 0:
    td_start = new_seg.rfind(b"<td", 0, idx)
    if td_start >= 0 and b"data-label" not in new_seg[td_start:idx]:
        label = b' data-label="Sell"'
        new_seg = new_seg[:td_start+3] + label + new_seg[td_start+3:]
        print("OK: sell")
    else:
        print("ALREADY or MISS: sell")
else:
    print("MISS: sell")

# Write back
content = content[:start] + bytes(new_seg) + content[end:]
with open(path, 'wb') as f:
    f.write(content)
print("\nWritten!")