import re
from pathlib import Path

today_html = Path('ai_earnings_today.html').read_text()
scanner_html = Path('scanner.html').read_text()

for fname, html in [('today.html', today_html), ('scanner.html', scanner_html)]:
    print(f'\n=== {fname} ===')
    idx = html.find('DRAM')
    if idx >= 0:
        # Find the div containing DRAM
        div_start = html.rfind('<div', 0, idx)
        print(f'DRAM found at {idx}, div starts at {div_start}')

        # Find end of this div
        depth = 1; i = div_start + 4
        while depth > 0 and i < len(html):
            if html[i:i+5] == '<div ' or html[i:i+4] == '<div>': depth += 1; i += 4
            elif html[i:i+6] == '</div>':
                depth -= 1
                if depth == 0:
                    print(f'DRAM div ends at {i+6}')
                    print(repr(html[div_start:i+6]))
                    break
            else: i += 1
    else:
        print('DRAM not found')
