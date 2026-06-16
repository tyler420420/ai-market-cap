path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

# Actual bytes from file - note: \' in file = single backslash then quote
old = b"html+='<td style=\\\"color:\\'+(r.days_left==0?\\'#ff4444\\':(r.days_left<=7?\\'#00ff88\\':\\'#ffcc00\\'))+\\\";font-weight:bold\\\">\\'+(r.days_left==0?\\'Today\\':r.days_left+\\'d\\')+\\'</td>"
# Wait, let me build from hex
actual_hex = bytes.fromhex('68746d6c2b3d273c7464207374796c653d5c22636f6c6f723a272b28722e646179735f6c6566743d3d303f2723666634343434273a28722e646179735f6c6566743c3d373f2723303066663838273a27236666636330302729292b273b666f6e742d7765696768743a626f6c645c223e272b28722e646179735f6c6566743d3d303f27546f646179273a722e646179735f6c6566742b276427292b273c2f74643e')
print("Actual:", repr(actual_hex))

# Find in content
idx = content.find(actual_hex)
if idx < 0:
    print("NOT FOUND by hex")
    idx = content.find(b"html+='<td style")
    print("Found by string:", idx)
    print("Content:", repr(content[idx:idx+200]))
else:
    print("Found at", idx)
    # Build new pattern - just change the color logic
    # Change: r.days_left<=7?'#00ff88':'#ffcc00' -> r.days_left<=14?'#ffcc00':(r.days_left<=35?'#58a6ff':'#00ff88')
    old_color_logic = b"(r.days_left<=7?\\'#00ff88\\':\\'#ffcc00\\')"
    new_color_logic = b"(r.days_left<=14?\\'#ffcc00\\':(r.days_left<=35?\\'#58a6ff\\':\\'#00ff88\\'))"
    replacement = actual_hex.replace(old_color_logic, new_color_logic)
    content = content.replace(actual_hex, replacement)
    with open(path, 'wb') as f:
        f.write(content)
    print("OK - replaced")