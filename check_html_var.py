with open('ai_earnings_57day_20260519_2256.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find renderTable function
start = c.find('function renderTable()')
end = c.find('document.addEventListener', start)
render_fn = c[start:end]

print('renderTable function:')
print(render_fn)
print()
# Count all uses of 'html' in the function
import re
html_uses = re.findall(r'\bhtml\b', render_fn)
print(f"'html' appears {len(html_uses)} times in renderTable")
for i, m in enumerate(re.finditer(r'\bhtml\b', render_fn)):
    ctx = render_fn[max(0,m.start()-15):m.start()+15]
    print(f'  #{i+1}: {repr(ctx)}')