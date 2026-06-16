path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

start = content.find(b"html+='<tr style")
end = content.find(b"sortBy('days_left');", start) + len(b"sortBy('days_left');")
seg = content[start:end]

# Find score pattern
idx = seg.find(b"font-size:1.3em")
if idx >= 0:
    chunk = seg[idx-50:idx+80]
    print("Score area:")
    print(chunk)
    print()
    # What are the actual bytes?
    for i, b in enumerate(chunk[:20]):
        print(f"  byte {i}: {b} ({chr(b) if 32 <= b < 127 else '?'})")
    print()

# Find days
idx = seg.find(b"r.days_left=='0")  # try different pattern
if idx >= 0:
    chunk = seg[idx-30:idx+80]
    print("Days area:")
    print(chunk)
    print()

# Check what the actual bytes are for the score td
idx = seg.find(b"<td><strong")
if idx >= 0:
    chunk = seg[idx:idx+120]
    print("First td:")
    print(chunk)
    print()
    for i, b in enumerate(chunk[:80]):
        print(f"  byte {i}: {b} ({chr(b) if 32 <= b < 127 else '?'})")