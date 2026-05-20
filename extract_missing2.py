import subprocess

result = subprocess.run(
    ['git', 'show', '6577033^:ai_earnings_scanner.py'],
    capture_output=True, text=True, encoding='utf-8', errors='replace',
    cwd=r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace'
)
old_code = result.stdout

start_marker = "html += '</style></head><body>'"
end_marker = 'html += "<button id=\\"chat-btn\\" onclick=\\"toggleChat()\\"'

start_idx = old_code.find(start_marker) + len(start_marker)
end_idx = old_code.find(end_marker)

missing = old_code[start_idx:end_idx]

# Write to file so we can inspect it
with open('missing_section.txt', 'w', encoding='utf-8') as f:
    f.write(missing)

print(f'Written {len(missing)} chars to missing_section.txt')
print(f'Line count: {missing.count(chr(10))}')

# Find how many html += lines it contains
line_count = missing.count('\n')
print(f'Total lines in section: {line_count}')

# Show the first few lines
lines = missing.split('\n')
print('\nFirst 5 lines:')
for l in lines[:5]:
    print(repr(l[:100]))