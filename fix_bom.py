import os, sys

for fname in ['ai_earnings_scanner.py', 'scanner_web.py']:
    with open(fname, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8-sig')  # strips UTF-8/UTF-16/UTF-32 BOM
    # Normalize to LF only (Unix line endings for git/Railway)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    with open(fname, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    print(f'{fname}: {len(text.splitlines())} lines, {len(text)} bytes')

# Update requirements
with open('requirements.txt', 'w', encoding='utf-8', newline='') as f:
    f.write('flask>=2.0,<3.0\nyfinance>=0.2.0\nrequests>=2.28.0\nbeautifulsoup4>=4.12.0\n')
print('requirements.txt updated')