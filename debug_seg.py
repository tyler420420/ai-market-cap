path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Get the segment
start = content.find("html+='<tr style")
end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
segment = content[start:end]

print(f'Segment len: {len(segment)}')

# Do replacements using the ACTUAL escaping from the file:
# The file uses \' for single quotes and \" for double quotes in double-quoted Python strings
# But get_seg.py showed \\" - let me check what the file actually has
print('First 200 chars of segment:')
print(repr(segment[:200]))
print()
print('Chars around shorts:')
idx = segment.find('short_int')
print(repr(segment[idx-20:idx+50]))