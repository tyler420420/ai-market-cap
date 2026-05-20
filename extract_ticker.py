import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('ai_earnings_web.html', 'r', encoding='utf-8', errors='replace') as f:
    c = f.read()

# Search for actual ticker content (NVDA, MSFT, etc in ticker context)
for kw in ['NVDA', 'SNOW', 'ticker-item', 'ticker-sym', 'ticker-price', 'AAPL', 'score']:
    idx = c.find(kw)
    if idx >= 0:
        print(f'{kw} at {idx}: {c[max(0,idx-50):idx+150]}')
        print()