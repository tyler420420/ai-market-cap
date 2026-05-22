with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Check all CSS rules for th
import re
style_start = c.find('<style>')
style_end = c.find('</style>')
css = c[style_start+7:style_end]
# Find all th rules
th_rules = re.findall(r'th[^{]*\{[^}]+\}', css)
for r in th_rules:
    print(repr(r))
print()

# Check body color vs th color
body_match = re.search(r'body\{[^}]*color:([^;]+)', css)
if body_match:
    print(f'Body color: {body_match.group(1)}')
    
# Check specificity - count selectors
print(f'Total CSS chars: {len(css):,}')
print(f'CSS position: {style_start} to {style_end}')
# Show around th rule
th_idx = css.find('th{')
if th_idx >= 0:
    print(f'th rule context: ...{css[max(0,th_idx-50):th_idx+120]}...')