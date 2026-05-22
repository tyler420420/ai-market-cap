import os
files = [
    r'C:\Users\Tyler_AI\Desktop\AI_Market_Cap_Scanner_v2.html',
    r'C:\Users\Tyler_AI\Desktop\test_scanner.html',
]
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            c = fh.read()
        th_idx = c.find('th{')
        gold_idx = c.find('#ffd700')
        print(f'=== {os.path.basename(f)} ===')
        print(f'  Size: {len(c):,} bytes')
        print(f'  th{{ CSS: {c[th_idx:th_idx+80]}')
        print(f'  Gold banner: {gold_idx >= 0}')
    except Exception as e:
        print(f'{f}: ERROR - {e}')