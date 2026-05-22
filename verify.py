c = open('ai_earnings_today.html', encoding='utf-8').read()
checks = {
    'Sticky bar': 'background:#1a2a1a' in c,
    'Last Updated:': 'Last Updated:' in c,
    'Title link to aismarketcap.com': 'href="https://aismarketcap.com"' in c,
    'How It Works button': 'How It Works' in c,
    'OG meta tags': 'og:title' in c,
    'Favicon link': '/static/logo.png' in c,
    'Description meta': 'description' in c
}
for k, v in checks.items():
    print(f"  {'OK' if v else 'MISSING'} {k}")