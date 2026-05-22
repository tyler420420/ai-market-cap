content = open('ai_earnings_scanner.py', encoding='utf-8').read()
checks = {
    '1. Meta/OG/favicon tags': '/static/logo.png' in content and 'og:title' in content,
    '2. Sticky bar at top': 'background:#1a2a1a;border-bottom:2px solid #2ea043' in content,
    '3. Title clickable to aismarketcap.com': 'href="https://aismarketcap.com"' in content,
    '4. Header desc simplified': 'Pre-earnings momentum scanner for Tech sector</div>' in content,
    '5. How It Works button (no glow)': 'How It Works' in content and 'box-shadow:none' in content,
    '6. Human-readable timestamp format': '%B %d, %Y at %I:%M %p PT' in content,
    '7. Last Updated: (no data source text)': '| Price data from' not in content and 'Last Updated' in content,
    '8. total_analysts = SB+B+H+S': 'total_analysts = total' in content,
}
print('ai_earnings_scanner.py checks:')
all_ok = True
for name, ok in checks.items():
    mark = '[OK]' if ok else '[MISSING]'
    print(f'  {mark} {name}')
    if not ok: all_ok = False
print()
if all_ok:
    print('ALL GOOD - scan will preserve everything')
else:
    print('WARNING: Some items missing - will revert on scan')