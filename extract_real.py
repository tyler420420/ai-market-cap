path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the renderTable segment
start = content.find("html+='<tr style")
end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
seg = content[start:end]

# Print the segment to a file
with open(r'C:\Users\Tyler_AI\ai-market-cap\js_seg_out.txt', 'w', encoding='utf-8') as f:
    f.write(seg)

# Also print what we need
print('Segment length:', len(seg))
print('First 100 chars:', repr(seg[:100]))
print()

# Find ticker
idx = seg.find("html+='<tr style")
if idx >= 0:
    print('Ticker start:', repr(seg[idx:idx+80]))
    print()

# Find days
idx = seg.find("r.days_left+'d')")
if idx >= 0:
    print('Days context:', repr(seg[idx-80:idx+40]))
    print()

# Find strong buy
idx = seg.find("r.sb+'</td>")
if idx >= 0:
    print('Strong buy context:', repr(seg[idx-40:idx+40]))