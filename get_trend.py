path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('r.squeeze?')
if idx >= 0:
    # Get the full line containing this
    start = content.rfind("html+='<td>", 0, idx)
    end = content.find("'</td>", idx) + 6
    seg = content[start:end]
    with open(r'C:\Users\Tyler_AI\ai-market-cap\trend_seg.txt', 'w', encoding='utf-8') as f:
        f.write(seg)
    print(repr(seg))