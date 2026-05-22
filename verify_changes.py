c = open('ai_earnings_today.html', encoding='utf-8').read()
checks = [
    ('4 IPO boxes', 'SOONEST IPO' in c and 'SpaceX' in c and 'OpenAI' in c and 'Anthropic' in c),
    ('Counters below buttons only (1x Strong Buy)', c.count('Strong Buy') == 1),
    ('Body padding 0', 'padding:0' in c and 'margin:0' in c),
    ('No max-width container', '1400px' not in c),
]
for name, ok in checks:
    print(f"  {'[OK]' if ok else '[FAIL]'} {name}")
print(f"\nAll checks passed" if all(ok for _, ok in checks) else "\nSome checks failed")