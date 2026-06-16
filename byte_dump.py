path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

# Find the start of the segment
idx = content.find(b"html+='<tr style")
if idx >= 0:
    chunk = content[idx:idx+80]
    print("Bytes:")
    for i, b in enumerate(chunk[:30]):
        c = chr(b) if 32 <= b < 127 else '?'
        print(f"  {i}: {b} ({c})")
    print()
    print("As string:")
    print(chunk.decode('utf-8', errors='replace')[:80])
    print()
    print("As repr:")
    print(repr(chunk[:80]))