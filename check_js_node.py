with open('ai_earnings_57day_20260519_2312.html', 'r', encoding='utf-8') as f:
    c = f.read()

import subprocess, tempfile, os, json

# Extract the first script block (the big one with rowsData)
s = c.find('<script>')
e = c.find('</script>')
script = c[s+8:e]

# Write to a temp .js file
with open('temp_script.js', 'w', encoding='utf-8') as f:
    f.write(script)

# Try to parse it with Node.js
result = subprocess.run(['node', '--check', 'temp_script.js'], capture_output=True, text=True)
print('Node.js syntax check:')
print(result.stdout)
print(result.stderr)
print('Return code:', result.returncode)