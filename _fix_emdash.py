mixed_badge = '<span style=\'background:#2a2a1a;border:1px solid #ffd700;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ffd700\'>Mixed</span>'

for path in ['C:/Users/Tyler_AI/ai-market-cap/ai_earnings_today.html',
             'C:/Users/Tyler_AI/Desktop/test_scanner.html']:
    html = open(path, 'r', encoding='utf-8').read()
    count = html.count('â€"')
    if count > 0:
        patched = html.replace('â€"', mixed_badge)
        open(path, 'w', encoding='utf-8').write(patched)
        print(f'{path}: fixed {count} occurrences')
    else:
        print(f'{path}: no broken em-dash found')
