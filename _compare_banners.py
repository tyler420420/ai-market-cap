import re
from pathlib import Path

today_html = Path('ai_earnings_today.html').read_text(encoding='utf-8')

# Find the AI pick section (between AI's Suggested Trade and stockTableBody)
ai_start = today_html.find("AI's Suggested Trade")
if ai_start < 0:
    ai_start = today_html.find("AI&#39;s Suggested Trade")

# Find stockTableBody after AI pick
tbody_pos = today_html.find('stockTableBody', ai_start)
print(f'AI Pick starts at {ai_start}, next stockTableBody at {tbody_pos}')

# Find the div that opens before AI pick
div_before = today_html.rfind('<div', 0, ai_start)
print(f'AI Pick div opens at {div_before}')

# Find the closing div that ends AI pick section
# Look for </div> that closes the pick-banner or </div> that precedes tbody
ai_section = today_html[div_before:tbody_pos]
print(f'AI Pick section: {len(ai_section)} chars')
print('Start:', repr(ai_section[:100]))
print('End:', repr(ai_section[-100:]))

# Also check scanner.html for the same
scanner_html = Path('scanner.html').read_text(encoding='utf-8')
ai_scanner = scanner_html.find("AI's Suggested Trade")
if ai_scanner < 0:
    ai_scanner = scanner_html.find("AI&#39;s Suggested Trade")
print(f'\nscanner.html AI Pick at: {ai_scanner}')
if ai_scanner >= 0:
    div_b = scanner_html.rfind('<div', 0, ai_scanner)
    tbody_s = scanner_html.find('stockTableBody', ai_scanner)
    print(f'Div opens at {div_b}, tbody at {tbody_s}')
    scanner_section = scanner_html[div_b:tbody_s]
    print(f'Scanner AI Pick section: {len(scanner_section)} chars')
    print('Scanner start:', repr(scanner_section[:100]))
    print('Scanner end:', repr(scanner_section[-100:]))
