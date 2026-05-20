with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 398 - needs 4-space indent to match the rest
lines[397] = '    html += \'.pick-banner{background:linear-gradient(135deg,#1a2a1a,#162016);border:1px solid #2ea043;border-radius:8px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;min-height:120px}\n\'

with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Fixed. Verifying...')
with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    lines2 = f.readlines()
for i in range(395, 402):
    print(f'{i+1}: {repr(lines2[i][:60])}')