import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

for kw in ['See the Scanner', 'scanner in action', 'screenshot', 'preview', 'Screenshot']:
    idx = content.find(kw)
    if idx >= 0:
        print(f'=== {kw} at {idx} ===')
        print(content[max(0, idx-50):idx+300])
        print()