path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find("html+='<tr style")
end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
seg = content[start:end]

print(f'Segment length: {len(seg)}')
# Check for data-label in the JS segment
print(f'data-label in segment: {seg.count("data-label=")}')

# Show first 200 chars
print(repr(seg[:200]))