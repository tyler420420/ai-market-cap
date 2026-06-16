path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

# The hex from dump shows: (r.days_left<=7?'#00ff88':'#ffcc00')
# In the file: \'#00ff88\' : single backslash + single-quote
old_color = b"(r.days_left<=7?\\'#00ff88\\':\\'#ffcc00\\')"
new_color = b"(r.days_left<=14?\\'#ffcc00\\':(r.days_left<=35?\\'#58a6ff\\':\\'#00ff88\\'))"

# Find it
idx = content.find(old_color)
print(f"Pattern found at: {idx}")
print(f"Old: {repr(old_color)}")

if idx >= 0:
    # Replace in-place using memory view for safety
    content = content.replace(old_color, new_color)
    with open(path, 'wb') as f:
        f.write(content)
    print("OK - written")
    # Verify
    with open(path, 'rb') as f:
        verify = f.read()
    idx2 = verify.find(old_color)
    print(f"Still present after write: {idx2 >= 0}")
    idx3 = verify.find(new_color)
    print(f"New pattern present: {idx3 >= 0}")
    if idx3 >= 0:
        print(repr(verify[idx3:idx3+100]))
else:
    print("MISS - dumping context")
    idx = content.find(b"days_left<=7")
    print(repr(content[idx:idx+100]))