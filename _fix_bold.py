import re

for path in ['C:/Users/Tyler_AI/ai-market-cap/ai_earnings_today.html',
             'C:/Users/Tyler_AI/Desktop/test_scanner.html']:
    html = open(path, 'r', encoding='utf-8').read()
    patched = html.replace('<span style="font-weight:bold">$', '<span>$')
    open(path, 'w', encoding='utf-8').write(patched)
    bold_still = '<span style="font-weight:bold">$' in patched
    print(f'{path}: bold removed = {not bold_still}')
