import re
from pathlib import Path

today_path = Path('ai_earnings_today.html')
today_html = today_path.read_text(encoding='utf-8')

# Find AI Pick section
ai_pick = re.search(r'<div class="pick-banner[^"]*"[^>]*>(.*?)</div>\s*<div class="pick-banner-2"', today_html, re.DOTALL)
if ai_pick:
    print('=== AI PICK ===')
    print(ai_pick.group(0)[:500])
else:
    # Try finding it another way
    idx = today_html.find('pick-banner')
    if idx >= 0:
        print('AI Pick context:', repr(today_html[idx:idx+500]))
    else:
        print('No pick-banner found')

print()

# Find runner-up
runner = re.search(r'<div class="pick-banner-2"[^>]*>(.*?)</div>\s*<div', today_html, re.DOTALL)
if runner:
    print('=== RUNNER UP ===')
    print(runner.group(0)[:500])
else:
    idx = today_html.find('pick-banner-2')
    if idx >= 0:
        print('Runner up context:', repr(today_html[idx:idx+500]))
    else:
        print('No pick-banner-2 found')
