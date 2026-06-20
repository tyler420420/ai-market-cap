import re

with open(r'C:\Users\Tyler_AI\Desktop\test_scanner_backup_20260617.html', encoding='utf-8') as f:
    backup = f.read()

# Check for corruption in the JS blocks
script_blocks = [(m.start(), m.end()) for m in re.finditer('<script>', backup)]
print(f'Script blocks: {len(script_blocks)}')

for i, (start, end) in enumerate(script_blocks):
    end_tag = backup.find('</script>', start)
    js = backup[start:end_tag]
    single_q = re.findall(r"style='[^']*'", js)
    if single_q:
        print(f'\nBlock {i+1}: {len(single_q)} single-quote style attrs')
        for m in single_q[:5]:
            print(f'  {m[:120]}')
    else:
        print(f'\nBlock {i+1}: CLEAN ({len(js)} chars)')

# Check static HTML rows for single quotes
tbody_start = backup.find('<tbody')
tbody_end = backup.find('</tbody>')
tbody_content = backup[tbody_start:tbody_end]
single_q_static = re.findall(r"style='[^']*'", tbody_content)
print(f'\nStatic tbody rows: {len(single_q_static)} single-quote style attrs')
for m in single_q_static[:3]:
    print(f'  {m[:120]}')
