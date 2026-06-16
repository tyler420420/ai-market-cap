path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

start = content.find(b"html+='<tr style")
end = content.find(b"sortBy('days_left');", start) + len(b"sortBy('days_left');")
seg = content[start:end]

# Build new segment by replacing bytes directly
# Each replacement is (old_bytes, new_bytes)

replacements = [
    # Score - actual bytes from debug
    (b'<td><strong style=\\"color:\'+c+\';font-size:1.3em\\">\'+r.score+\'</strong></td>',
     b'<td data-label="Score"><strong style=\\"color:\'+c+\'\\">\'+r.score+\'</strong></td>'),
    
    # Days
    (b'<td style=\\"color:\'+(r.days_left==0',
     b'<td data-label="Days" style=\\"color:\'+(r.days_left==0'),
    
    # 3 Day Target
    (b"<td><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\\"color:#00ff88\\">+'+r.pe_upside+'%</span></td>",
     b'<td data-label="3 Day"><strong>$'+Math.floor(b"r.pe_target")+b'</strong> <span style=\\"color:#00ff88\\">+\'+r.pe_upside+\'%</span></td>'),
    
    # 7 Day
    (b"<td>$'+Math.floor(r['3d'])+' <span style=\\"color:#00ff88\\">+'+r['3d_up']+'%</span></td>",
     b"<td data-label='7 Day'>$'+Math.floor(r['3d'])+' <span style=\\"color:#00ff88\\">+'+r['3d_up']+'%</span></td>"),
    
    # 14 Day
    (b"<td>$'+Math.floor(r['5d'])+' <span style=\\"color:#00ff88\\">+'+r['5d_up']+'%</span></td>",
     b"<td data-label='14 Day'>$'+Math.floor(r['5d'])+' <span style=\\"color:#00ff88\\">+'+r['5d_up']+'%</span></td>"),
    
    # Strong Buy
    (b'<td style=\\"color:#00ff88\\">\'+r.sb+\'</td>',
     b'<td data-label="Strong Buy" style=\\"color:#00ff88\\">\'+r.sb+\'</td>'),
    
    # Buy
    (b'<td style=\\"color:#58a6ff\\">\'+r.buy+\'</td>',
     b'<td data-label="Buy" style=\\"color:#58a6ff\\">\'+r.buy+\'</td>'),
    
    # Hold
    (b'<td style=\\"color:#ffcc00\\">\'+r.hold+\'</td>',
     b'<td data-label="Hold" style=\\"color:#ffcc00\\">\'+r.hold+\'</td>'),
    
    # Sell
    (b'<td style=\\"color:#ff6b6b\\">\'+r.sell+\'</td>',
     b'<td data-label="Sell" style=\\"color:#ff6b6b\\">\'+r.sell+\'</td>'),
    
    # Shorts
    (b"<td style=\\'color:#fff\\'>'+r.short_int+'%</td>",
     b"<td data-label='Shorts' style=\\'color:#fff\\'>'+r.short_int+'%</td>"),
    
    # IV
    (b"<td style=\\'color:#fff\\'>'+r.iv+'%</td>",
     b"<td data-label='IV' style=\\'color:#fff\\'>'+r.iv+'%</td>"),
    
    # Trend
    (b"<td>+(r.squeeze?",
     b"<td data-label='Trend'>+(r.squeeze?"),
]

new_seg = seg
changes = 0
for old, new in replacements:
    if old in new_seg:
        new_seg = new_seg.replace(old, new, 1)
        changes += 1
        print(f'OK: {old[:40]}')
    else:
        print(f'MISS: {old[:50]}')

print(f'\nTotal: {changes}/{len(replacements)}')
if changes >= 10:
    content = content[:start] + new_seg + content[end:]
    with open(path, 'wb') as f:
        f.write(content)
    print('Written!')
else:
    print('Not enough - check')