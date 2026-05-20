with open('ai_earnings_57day_20260519_2256.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Inject debug logging right at the start of the first script block
# Add console.log statements to track execution
debug_script = """
console.log('SCRIPT START - rowsData exists:', typeof rowsData !== 'undefined');
console.log('SCRIPT START - rowsData length:', typeof rowsData !== 'undefined' ? rowsData.length : 'N/A');
console.log('SCRIPT START - tbody element:', document.getElementById('stockTableBody'));
"""

# Find the start of the first script content
s = c.find('<script>')
e = c.find('</script>')

# Insert debug at the start of the script content (after <script>var rowsData=)
# Actually, insert right after 'var rowsData=' + show that we have data
# The script starts with 'var rowsData=' - let's add after the JSON array
# Find where the array closes: ];var sortCol
arr_end = c.find('];var sortCol')
# Insert debug right there
new_c = c[:arr_end+2] + '\nconsole.log("After JSON parse - rowsData:", rowsData ? rowsData.length + " rows" : "UNDEFINED");\n' + c[arr_end+2:]

with open('ai_earnings_57day_20260519_2256_debug.html', 'w', encoding='utf-8') as f:
    f.write(new_c)

print(f'Original: {len(c)} chars, New: {len(new_c)} chars')
print(f'Inserted at position: {arr_end+2}')