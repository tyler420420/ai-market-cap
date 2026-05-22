content = open('ai_earnings_scanner.py').read()
idx = content.find("mktcap'}")
print('mktcap} found at:', idx)
if idx >= 0:
    print(repr(content[idx-20:idx+50]))
    
idx = content.find("r.mktcap'}")
print('r.mktcap} found at:', idx)
if idx >= 0:
    print(repr(content[idx-20:idx+50]))

# Also check what the actual pattern looks like in getVal
idx = content.find("getVal")
js_chunk = content[idx:idx+600]
# Find the closing of the m object
m_end = js_chunk.find("'};")
print('\ngetVal m object ends at:')
print(repr(js_chunk[m_end-5:m_end+5]))