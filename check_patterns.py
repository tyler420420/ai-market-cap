c = open('ai_earnings_today.html', encoding='utf-8').read()

# Find and show exact patterns before removing
idx1 = c.find('Watch</span></span><a href="/about"')
idx2 = c.find('Watch</span></span></div><div style="display:flex')

print(f'Pattern 1 (before How It Works): {repr(c[idx1-300:idx1+50])}')
print(f'\nPattern 2 (before IPO boxes): {repr(c[idx2-300:idx2+50])}')