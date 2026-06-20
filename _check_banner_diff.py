import re
from pathlib import Path

today_html = Path('ai_earnings_today.html').read_text(encoding='utf-8')
scanner_html = Path('scanner.html').read_text(encoding='utf-8')

# Find the actual div containing AI pick in today.html (not the CSS)
# Look for the first div with class=pick-banner that has the actual content
today_pick_start = today_html.find("AI's Suggested Trade")
scanner_pick_start = scanner_html.find("AI's Suggested Trade")
if scanner_pick_start < 0:
    scanner_pick_start = scanner_html.find("AI&#39;s Suggested Trade")

# Find the div that contains this text
today_div = today_html.rfind('<div', 0, today_pick_start)
scanner_div = scanner_html.rfind('<div', 0, scanner_pick_start)

# Find where this div ends (next </div> that closes it)
# The div ends when we hit </div> that isn't nested
def find_div_end(html, start):
    depth = 1
    i = start + 4  # skip past '<div'
    while depth > 0 and i < len(html):
        if html[i:i+5] == '<div ' or html[i:i+4] == '<div>':
            depth += 1
            i += 4
        elif html[i:i+6] == '</div>':
            depth -= 1
            if depth == 0:
                return i + 6
            i += 6
        else:
            i += 1
    return len(html)

today_pick_end = find_div_end(today_html, today_div)
scanner_pick_end = find_div_end(scanner_html, scanner_div)

today_section = today_html[today_div:today_pick_end]
scanner_section = scanner_html[scanner_div:scanner_pick_end]

print(f'today.html AI pick div: {len(today_section)} chars')
print(f'scanner.html AI pick div: {len(scanner_section)} chars')

# Are they the same?
if today_section == scanner_section:
    print('\nIDENTICAL - AI pick is already up to date!')
else:
    print('\nDIFFERENT - need to update!')
    # Find the key data differences
    today_ticker = re.search(r'font-weight:bold;color:#fff">([A-Z]+)</span>', today_section)
    scanner_ticker = re.search(r'font-weight:bold;color:#fff">([A-Z]+)</span>', scanner_section)
    today_price = re.search(r'Buy Price.*?\$([0-9,]+)', today_section)
    scanner_price = re.search(r'Buy Price.*?\$([0-9,]+)', scanner_section)
    print(f'today: ticker={today_ticker.group(1) if today_ticker else "?"}, price=${today_price.group(1) if today_price else "?"}')
    print(f'scanner: ticker={scanner_ticker.group(1) if scanner_ticker else "?"}, price=${scanner_price.group(1) if scanner_price else "?"}')
