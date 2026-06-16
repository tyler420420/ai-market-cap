path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Read actual content for the js row
idx = content.find("html+=\'<tr style")
if idx < 0:
    print('not found')
else:
    # Extract 1500 chars of the row building section
    segment = content[idx:idx+1500]
    print(f'Segment length: {len(segment)}')
    print(f'First 200: {repr(segment[:200])}')
    print(f'Last 200: {repr(segment[-200:])}')
    # Write segment to a temp file for inspection
    with open(r'C:\Users\Tyler_AI\ai-market-cap\temp_segment.txt', 'w', encoding='utf-8') as f:
        f.write(segment)
    print('Segment written to temp_segment.txt')