import re

for path in ['C:/Users/Tyler_AI/ai-market-cap/ai_earnings_today.html',
             'C:/Users/Tyler_AI/Desktop/test_scanner.html']:
    html = open(path, 'r', encoding='utf-8').read()
    # Add hover to Trade on Kraken buttons in pick banners
    old = 'Trade on Kraken</a>'
    new = 'Trade on Kraken</a>'
    # Find the specific button pattern - needs onmouseover/onmouseout added
    patched = html.replace(
        'style="display:inline-block;background:#5741d9;color:#fff;padding:8px 18px;border-radius:6px;font-weight:bold;text-decoration:none;font-size:0.9em;margin-left:auto">Trade',
        'style="display:inline-block;background:#5741d9;color:#fff;padding:8px 18px;border-radius:6px;font-weight:bold;text-decoration:none;font-size:0.9em;margin-left:auto" onmouseover="this.style.background=\'#6e55e0\'" onmouseout="this.style.background=\'#5741d9\'">Trade'
    )
    open(path, 'w', encoding='utf-8').write(patched)
    print(f'{path}: patched')
