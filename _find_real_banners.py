import re
from pathlib import Path

today_html = Path('ai_earnings_today.html').read_text(encoding='utf-8')
scanner_html = Path('scanner.html').read_text(encoding='utf-8')

def find_div_end(html, start):
    depth = 1; i = start + 4
    while depth > 0 and i < len(html):
        if html[i:i+5] == '<div ' or html[i:i+4] == '<div>':
            depth += 1; i += 4
        elif html[i:i+6] == '</div>':
            depth -= 1
            if depth == 0: return i + 6
            i += 6
        else: i += 1
    return len(html)

# Find runner-up in both files (pick-banner with 2nd pick or #2 pick)
for fname, html in [('today.html', today_html), ('scanner.html', scanner_html)]:
    print(f'\n=== {fname} ===')
    idx = 0
    while True:
        idx = html.find('pick-banner', idx)
        if idx < 0: break
        # Skip if this is inside a <style> tag
        style_before = html.rfind('<style', 0, idx)
        style_end = html.find('</style>', style_before) if style_before >= 0 else -1
        if style_before >= 0 and style_before < idx < style_end:
            idx += 1; continue
        div_s = html.rfind('<div', 0, idx)
        div_e = find_div_end(html, div_s)
        content = html[div_s:div_e]
        if len(content) > 200:  # Skip tiny divs (CSS-related)
            print(f'  Real pick-banner div: {div_s}-{div_e} ({len(content)} chars)')
            print(f'  Content preview: {content[:300]}')
        idx += 1
