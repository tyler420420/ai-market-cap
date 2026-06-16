path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the renderTable section - it starts with "function renderTable" and ends with "sortBy('days_left');"
start = content.find("html+='<tr style=\"background:'+bg+'\"")
if start < 0:
    start = content.find("html+='<tr style=\"+bg+'\"")
if start < 0:
    start = content.find("html+='<tr style=background:'")

print(f"Start index: {start}")
if start >= 0:
    # The end is marked by sortBy('days_left');
    end = content.find("sortBy('days_left');", start)
    if end >= 0:
        end += len("sortBy('days_left');")
        segment = content[start:end]
        print(f"Segment length: {len(segment)}")
        print(f"First 200 chars: {repr(segment[:200])}")
        print(f"Last 200 chars: {repr(segment[-200:])}")
    else:
        print('End not found')
else:
    # Try to find it another way
    idx = content.find("html+='<tr style")
    print(f"html+='<tr style found at: {idx}")
    if idx >= 0:
        segment = content[idx:idx+200]
        print(repr(segment))