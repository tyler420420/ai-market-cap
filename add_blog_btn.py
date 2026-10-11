content = open(r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html', 'r', encoding='utf-8').read()
old = "/about' style='background:#ffd700"
new = "/blog' style='background:#e63946;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff' onmouseover='this.style.background=\"#ff6b6b\"' onmouseout='this.style.background=\"#e63946\"'>Blog</a><a href='/about' style='background:#ffd700"
if old in content:
    content = content.replace(old, new, 1)
    open(r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html', 'w', encoding='utf-8').write(content)
    print('Done - Blog button added')
else:
    print('Pattern not found, searching...')
    idx = content.find('ffd700')
    print('ffd700 at index:', idx)
    if idx > 0:
        print(content[max(0,idx-30):idx+150])
