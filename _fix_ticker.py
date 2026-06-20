for path in ['C:/Users/Tyler_AI/ai-market-cap/ai_earnings_today.html',
             'C:/Users/Tyler_AI/Desktop/test_scanner.html']:
    html = open(path, 'r', encoding='utf-8').read()
    patched = html.replace('scroll-ticker 500s', 'scroll-ticker 400s')
    open(path, 'w', encoding='utf-8').write(patched)
    print(f'{path}: 500s -> 400s')
