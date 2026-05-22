content = open('ai_earnings_scanner.py').read()
# Find the exact pattern
idx = content.find("color:'+c+'")
if idx >= 0:
    snippet = content[idx-5:idx+60]
    print(repr(snippet))
    # Replace in place
    old = snippet
    new = snippet.replace("color:'+c+'", "color:'+c+';font-size:1.3em", 1)
    if new != old:
        content = content.replace(old, new, 1)
        with open('ai_earnings_scanner.py', 'w') as f:
            f.write(content)
        import ast
        ast.parse(content)
        print('OK - score 1.3em')
    else:
        print('Could not replace')
else:
    print('Not found')