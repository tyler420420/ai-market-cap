import re
from pathlib import Path

today_html = Path('ai_earnings_today.html').read_text(encoding='utf-8')

# Find AI's Suggested Trade section start
ai_start = today_html.find("AI's Suggested Trade")
if ai_start < 0:
    ai_start = today_html.find("AI&#39;s Suggested Trade")

# Go back to find the opening div
before = today_html[:ai_start]
div_before = before.rfind('<div')
print(f'AI Pick starts at div #{div_before}')

# Find the next "Runner up" or "Runner-Up" text after AI pick
runner = today_html.find("Runner", ai_start)
runner2 = today_html.find("runner", ai_start)
runner = min(r for r in [runner, runner2] if r > 0)
print(f'Runner up text at: {runner}')
print('Runner up context:', repr(today_html[runner:runner+400]))
print()

# Check if runner is inside a pick-banner-2 div
pick2_before = today_html[:runner]
pick2_div = pick2_before.rfind('<div')
print(f'Runner-up div starts at: {pick2_div}')

# Find end of the runner-up section (before tbody or next major div)
tbody_pos = today_html.find('stockTableBody')
print(f'stockTableBody at: {tbody_pos}')

# Extract both banners
ai_section = today_html[div_before:pick2_div]
runner_section = today_html[pick2_div:tbody_pos]

print(f'\n=== AI PICK SECTION ({len(ai_section)} chars) ===')
print(ai_section[:600])

print(f'\n=== RUNNER UP SECTION ({len(runner_section)} chars) ===')
print(runner_section[:600])
