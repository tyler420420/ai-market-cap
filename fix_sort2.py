with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the exact pattern
import re
# Find tbody.innerHTML=html followed by } and then html += '</script>'
pattern = r"(tbody\.innerHTML=html;)\}"
replacement = r"\1document.querySelectorAll('th[data-col]').forEach(function(th){th.style.cursor='pointer';th.title='Click to sort';});updateArrows();}"

new_c, count = re.subn(pattern, replacement, c)
print(f'Replacements: {count}')
if count > 0:
    with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
        f.write(new_c)
    print('File updated')
else:
    # Find what's actually there
    idx = c.find('tbody.innerHTML=html')
    print('Context around tbody.innerHTML:')
    print(repr(c[idx:idx+50]))