path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find("html+='<tr style")
end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
seg = content[start:end]

# Find patterns for MISS items
# Score: empty attr td
idx = seg.find("';font-size:1.3em\">")
if idx >= 0:
    print(f'Score pattern at {idx}: {repr(seg[idx-30:idx+50])}')
    print(f'  Full td: {repr(seg[idx-40:idx+60])}')

# Days
idx = seg.find("r.days_left+'d')")
if idx >= 0:
    print(f'\nDays pattern: {repr(seg[idx-80:idx+30])}')

# 3 Day
idx = seg.find("r.pe_target)+")
if idx >= 0:
    print(f'\n3 Day pattern: {repr(seg[idx-30:idx+80])}')

# Strong Buy
idx = seg.find("r.sb+'</td>")
if idx >= 0:
    print(f'\nStrong Buy pattern: {repr(seg[idx-30:idx+40])}')

# Shorts
idx = seg.find("r.short_int+'%")
if idx >= 0:
    print(f'\nShorts pattern: {repr(seg[idx-30:idx+50])}')

# Trend
idx = seg.find("r.squeeze?")
if idx >= 0:
    print(f'\nTrend pattern: {repr(seg[idx-30:idx+30])}')