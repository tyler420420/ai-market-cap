with open('scanner.html', encoding='utf-8') as f:
    html = f.read()

# Remove the sortBy('days_left'); call that triggers broken renderTable
# The JS ends with: ...sortBy('days_left');</script>
# We want: ...;</script>
html = html.replace("sortBy('days_left');</script>", ";</script>")

with open('scanner.html', 'w', encoding='utf-8') as f:
    f.write(html)

import shutil
shutil.copy('scanner.html', r'C:\Users\Tyler_AI\Desktop\test_scanner.html')

print(f'scanner.html: {len(html)} bytes')

# Verify the ending
js_end = html.rfind('</script>')
print(f'Last 80 chars: {repr(html[js_end-80:js_end+10])}')
