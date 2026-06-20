import re
from pathlib import Path

today_html = Path('ai_earnings_today.html').read_text(encoding='utf-8')

# Find all occurrences of stockTableBody
idx = 0
count = 0
while True:
    idx = today_html.find('stockTableBody', idx)
    if idx < 0: break
    print(f'stockTableBody at {idx}')
    idx += 1
    count += 1
print(f'Total: {count}')

# Find AI's Suggested Trade
ai_start = today_html.find("AI's Suggested Trade")
if ai_start < 0:
    ai_start = today_html.find("AI&#39;s Suggested Trade")
print(f"AI's Suggested Trade at: {ai_start}")

# Check what's between stockTableBody and AI pick
print(f'\nBetween tbody and AI pick:')
print(today_html[8660:8660+200])
