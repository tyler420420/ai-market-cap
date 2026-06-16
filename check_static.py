path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the JS renderTable segment
idx = content.find("rowsData.forEach")
seg = content[idx:idx+3000]
print(repr(seg[:400]))
print()

# Count data-label
count = seg.count('data-label=')
print(f'data-label count: {count}')

# Check if the HTML static rows have data-labels
idx2 = content.find('<tr style')
seg2 = content[idx2:idx2+500]
print(repr(seg2[:300]))