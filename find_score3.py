content = open('ai_earnings_scanner.py').read()
idx = content.find("color:'+c+'")
print('Found at:', idx)
if idx >= 0:
    print(repr(content[idx-10:idx+60]))