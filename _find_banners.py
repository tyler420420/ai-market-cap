import re
from pathlib import Path

today_html = Path('ai_earnings_today.html').read_text(encoding='utf-8')

# Look for "AI's" or "AI Pick" text
for kw in ["AI's", "AI Pick", "AI's Next", "Top Pick", "Runner", "runner-up"]:
    idx = today_html.find(kw)
    if idx >= 0:
        print(f'=== {kw} at {idx} ===')
        print(repr(today_html[idx:idx+400]))
        print()
        break

# Check what comes after the header / before the table
idx = today_html.find('stockTableBody')
if idx >= 0:
    print('=== Before tbody (last 800 chars) ===')
    print(repr(today_html[max(0,idx-800):idx]))
