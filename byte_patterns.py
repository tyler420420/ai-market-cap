path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

start = content.find(b"html+='<tr style")
end = content.find(b"sortBy('days_left');", start) + len("sortBy('days_left');")
seg = content[start:end]

# Find score pattern
idx = seg.find(b"font-size:1.3em")
if idx >= 0:
    print("Score:")
    print(repr(seg[idx-60:idx+60]))
    print()

# Find 3 day pattern
idx = seg.find(b"pe_target)+' |")
if idx >= 0:
    print("3 Day:")
    print(repr(seg[idx-20:idx+100]))
    print()

# Find strong buy
idx = seg.find(b"color:#00ff88")
if idx >= 0:
    print("Strong Buy:")
    print(repr(seg[idx-30:idx+50]))
    print()

# Find shorts
idx = seg.find(b"color:#fff")
if idx >= 0:
    print("Shorts:")
    print(repr(seg[idx-30:idx+50]))
    print()

# Find trend
idx = seg.find(b"r.squeeze?")
if idx >= 0:
    print("Trend:")
    print(repr(seg[idx-30:idx+30]))