html = open('ai_earnings_today.html').read()

# Add cursor:pointer to th in stockTable
# Find the th CSS rule and add cursor:pointer
old = '#stockTable thead tr th{position:relative;user-select:none;font-size:0.82em;color:#8b949e;text-align:left;padding:10px 12px;border-bottom:2px solid #30363d;white-space:nowrap}'
new = '#stockTable thead tr th{position:relative;user-select:none;font-size:0.82em;color:#8b949e;text-align:left;padding:10px 12px;border-bottom:2px solid #30363d;white-space:nowrap;cursor:pointer}'
patched = html.replace(old, new)
print('th cursor patch:', patched != html)

# Also add a visual sort indicator (▲/▼) for active column
# The updateArrows function handles this via CSS classes - let's verify those exist
has_sorted = 'sorted-asc' in patched and 'sorted-desc' in patched
print('Sort arrow CSS exists:', has_sorted)

open('ai_earnings_today.html', 'w').write(patched)
open('C:/Users/Tyler_AI/Desktop/test_scanner.html', 'w').write(patched)
print('Done')
