path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find("html+='<tr style")
print(f"html+='<tr style at: {idx}")
if idx >= 0:
    # Show 300 chars
    segment = content[idx:idx+300]
    print(repr(segment))
    # Now try to find what it actually contains - maybe the escape sequences are different
    # Let's search for the pattern byte-by-byte
    import re
    m = re.search(r"html\+\='<tr style.{0,5}background.{0,5}\+bg", content)
    if m:
        print(f"Regex found at: {m.start()}")
        print(repr(content[m.start():m.start()+300]))
    else:
        print('Regex not found')
        # Try without quotes
        idx2 = content.find('<tr style')
        print(f'<tr style at: {idx2}')
        if idx2 >= 0:
            print(repr(content[idx2:idx2+100]))