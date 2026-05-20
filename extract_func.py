import subprocess

result = subprocess.run(
    ['git', 'show', '6577033^:ai_earnings_scanner.py'],
    capture_output=True, text=True, encoding='utf-8', errors='replace',
    cwd=r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace'
)
old_code = result.stdout

# Find the generate_html_report function
start_idx = old_code.find('def generate_html_report')
# Find the chat button section
end_idx = old_code.find('html += "<button id=\\"chat-btn\\"')

func_content = old_code[start_idx:end_idx]

# Write to file
with open('old_generate_function.txt', 'w', encoding='utf-8') as f:
    f.write(func_content)

print(f'Written {len(func_content)} chars')
print(f'Lines: {func_content.count(chr(10))}')

# Show lines from 370 onwards
lines = func_content.split('\n')
print('\n=== FUNCTION CONTENT (lines 7 onwards from html += body) ===')
found_body = False
for i, l in enumerate(lines):
    if "html += '</style></head><body>'" in l:
        found_body = True
    if found_body and i >= 10:
        print(f'  {l[:120]}')