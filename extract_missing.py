import subprocess

result = subprocess.run(
    ['git', 'show', '6577033^:ai_earnings_scanner.py'],
    capture_output=True, text=True, encoding='utf-8', errors='replace',
    cwd=r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace'
)
old_code = result.stdout

# Find the section between html += '</style></head><body>' and the OLD chat button
start_marker = "html += '</style></head><body>'"
end_marker = 'html += "<button id=\\"chat-btn\\" onclick=\\"toggleChat()\\"'

start_idx = old_code.find(start_marker) + len(start_marker)
end_idx = old_code.find(end_marker)

missing = old_code[start_idx:end_idx]
print(f'Missing section: {len(missing)} chars')
print()
print('=== MISSING HTML SECTION ===')
print(missing)