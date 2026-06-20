with open('scanner.html', encoding='utf-8') as f:
    lines = f.read().split('\n')

# Remove conflict lines manually
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if line == '<<<<<<< HEAD':
        # Skip until after the ======= marker
        i += 1
        while i < len(lines) and lines[i] != '=======':
            i += 1
        i += 1  # skip =======
        # Now skip remote lines until >>>>>>>
        while i < len(lines) and not lines[i].startswith('>>>>>>>'):
            i += 1
        i += 1  # skip >>>>>>>
    elif line == '=======':
        # Conflict marker in second conflict - skip until >>>>>>>
        i += 1
        while i < len(lines) and not lines[i].startswith('>>>>>>>'):
            i += 1
        i += 1
    else:
        new_lines.append(line)
        i += 1

content = '\n'.join(new_lines)

# Verify no conflict markers remain
import re
remaining = re.findall(r'<<<<<<<|=======|>>>>>>>', content)
print(f'Remaining conflict markers: {len(remaining)}')

with open('scanner.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
