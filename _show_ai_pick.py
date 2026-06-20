import re
from pathlib import Path

today_html = Path('ai_earnings_today.html').read_text(encoding='utf-8')
scanner_html = Path('scanner.html').read_text(encoding='utf-8')

# Get today.html AI pick section
today_ai_div = 25731
today_tbody = 28502
today_section = today_html[today_ai_div:today_tbody]
print(f'today.html AI pick: {len(today_section)} chars')
print('today.ai starts:', repr(today_section[:200]))
print('today.ai ends:', repr(today_section[-200:]))

# Does today.html have a Runner-Up pick too?
runner_idx = today_html.find('Runner', today_ai_div)
runner2_idx = today_html.find('runner', today_ai_div)
if runner_idx < 0: runner_idx = 999999
if runner2_idx < 0: runner2_idx = 999999
runner_next = min(runner_idx, runner2_idx)
runner_next = min(r for r in [runner_next, today_tbody] if r > today_ai_div)
print(f'\nRunner text found after AI pick? idx={runner_next}, tbody={today_tbody}')
if runner_next < today_tbody:
    print('Runner context:', repr(today_html[runner_next:runner_next+100]))

# Now extract the scanner.html AI pick and see its full content
scanner_ai_div = 25735
scanner_tbody = 29527
scanner_section = scanner_html[scanner_ai_div:scanner_tbody]
print(f'\nscanner.html AI pick: {len(scanner_section)} chars')
print('scanner starts:', repr(scanner_section[:200]))
print('scanner ends:', repr(scanner_section[-200:]))

# Show the full content of both
print(f'\n=== TODAY AI PICK ({len(today_section)} chars) ===')
print(today_section)
