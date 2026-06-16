path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find("html+='<tr style")
end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
seg = content[start:end]

with open(r'C:\Users\Tyler_AI\ai-market-cap\js_seg.txt', 'w', encoding='utf-8') as f:
    f.write(seg)

print('Written. Length:', len(seg))