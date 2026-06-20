import re
from pathlib import Path

today_html = Path('ai_earnings_today.html').read_text(encoding='utf-8')
scanner_html = Path('scanner.html').read_text(encoding='utf-8')

def find_div_end(html, start):
    depth = 1
    i = start + 4
    while depth > 0 and i < len(html):
        if html[i:i+5] == '<div ' or html[i:i+4] == '<div>':
            depth += 1; i += 4
        elif html[i:i+6] == '</div>':
            depth -= 1
            if depth == 0: return i + 6
            i += 6
        else:
            i += 1
    return len(html)

# Find AI pick divs
today_pick_start = today_html.find("AI's Suggested Trade")
scanner_pick_start = scanner_html.find("AI's Suggested Trade")
if scanner_pick_start < 0:
    scanner_pick_start = scanner_html.find("AI&#39;s Suggested Trade")

today_div = today_html.rfind('<div', 0, today_pick_start)
scanner_div = scanner_html.rfind('<div', 0, scanner_pick_start)

today_pick_end = find_div_end(today_html, today_div)
scanner_pick_end = find_div_end(scanner_html, scanner_div)

today_pick = today_html[today_div:today_pick_end]
scanner_pick = scanner_html[scanner_div:scanner_pick_end]

print(f'AI pick: today={len(today_pick)} chars, scanner={len(scanner_pick)} chars')
if today_pick != scanner_pick:
    print('AI PICK NEEDS UPDATE')
    t = re.search(r'font-weight:bold;color:#fff">([A-Z]+)</span>', today_pick)
    p = re.search(r'Buy Price.*?\$([0-9,]+)', today_pick)
    print(f'  today: {t.group(1) if t else "?"} @ ${p.group(1) if p else "?"}')
    t2 = re.search(r'font-weight:bold;color:#fff">([A-Z]+)</span>', scanner_pick)
    p2 = re.search(r'Buy Price.*?\$([0-9,]+)', scanner_pick)
    print(f'  scanner: {t2.group(1) if t2 else "?"} @ ${p2.group(1) if p2 else "?"}')

# Check for runner-up / 2nd pick in today.html
# Look for any other pick-banner divs after the first
today_all_picks = []
idx = 0
while True:
    idx = today_html.find('pick-banner', idx)
    if idx < 0: break
    div_s = today_html.rfind('<div', 0, idx)
    div_e = find_div_end(today_html, div_s)
    content = today_html[div_s:div_e]
    if "AI's" not in content:
        today_all_picks.append((div_s, div_e, content[:100]))
    idx += 1

scanner_all_picks = []
idx = 0
while True:
    idx = scanner_html.find('pick-banner', idx)
    if idx < 0: break
    div_s = scanner_html.rfind('<div', 0, idx)
    div_e = find_div_end(scanner_html, div_s)
    content = scanner_html[div_s:div_e]
    if "AI's" not in content:
        scanner_all_picks.append((div_s, div_e, content[:100]))
    idx += 1

print(f'\nOther pick-banner divs: today={len(today_all_picks)}, scanner={len(scanner_all_picks)}')
for s, e, c in today_all_picks:
    print(f'  today: {s}-{e}: {c[:80]}')
for s, e, c in scanner_all_picks:
    print(f'  scanner: {s}-{e}: {c[:80]}')
