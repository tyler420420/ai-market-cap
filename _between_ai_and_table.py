from pathlib import Path
html = Path('ai_earnings_today.html').read_text()
idx = html.find('<table id="stockTable">')
ai_start = html.find("AI's Suggested Trade")
ai_div_start = html.rfind('<div', 0, ai_start)
between = html[26761:idx]
print('Between AI pick end and table (200 chars):')
print(repr(between[:200]))
