with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Check thead for inline th styles
thead_start = c.find('<thead>')
thead_end = c.find('</thead>')
print('THEAD HTML:')
print(repr(c[thead_start:thead_end+8]))
print()

# Check if style tag has the CSS
style_start = c.find('<style>')
style_end = c.find('</style>')
print('STYLE TAG LOCATION:')
print(f'Style starts at: {style_start}, ends at: {style_end}')
print(f'Style length: {style_end - style_start:,} chars')
print()

# Check if body color is overriding
body_idx = c.find('body{')
print('BODY CSS:')
print(repr(c[body_idx:body_idx+200]))