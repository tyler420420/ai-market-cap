import re
from pathlib import Path

today_html = Path('ai_earnings_today.html').read_text(encoding='utf-8')

ai_start = today_html.find("AI's Suggested Trade")
if ai_start < 0:
    ai_start = today_html.find("AI&#39;s Suggested Trade")

before = today_html[:ai_start]
div_before = before.rfind('<div')
print(f'AI Pick div starts at: {div_before}')

# Find "run" or "2nd" or "next" near the AI pick
for kw in ["Runner", "run", "2nd", "second", "Next", "second", "Pick 2"]:
    idx = today_html.find(kw, ai_start + 10)
    if idx > 0 and idx < ai_start + 1000:
        print(f'{kw} found at {idx}:', repr(today_html[idx-5:idx+100]))

# The AI pick ends right before the table (stockTableBody)
tbody_pos = today_html.find('stockTableBody')
print(f'stockTableBody at: {tbody_pos}')

# Look for the closing div of the pick section
# It might be the next </div> after the AI pick content
ai_section_end = tbody_pos
ai_section = today_html[div_before:ai_section_end]
print(f'\nAI Pick section ({len(ai_section)} chars):')
print(ai_section[:500])
print('...')
print(ai_section[-200:])
