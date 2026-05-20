import subprocess

result = subprocess.run(
    ['git', 'show', '6577033^:ai_earnings_scanner.py'],
    capture_output=True, text=True, encoding='utf-8', errors='replace',
    cwd=r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace'
)
old_code = result.stdout
lines = old_code.split('\n')

print('=== OLD HEADERS DEFINITION (lines 446-465) ===')
for i in range(445, 465):
    print(f'{i+1}: {lines[i][:140]}')